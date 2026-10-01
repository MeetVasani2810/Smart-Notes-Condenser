"""
services.py
-----------
Business logic layer.

Connects the FastAPI endpoint to the model by:
  1. Selecting the correct prompt strategy for the requested task.
  2. Building the full prompt (or per-item prompts for quiz/flashcards).
  3. Calling generate_text() to run inference with task-specific parameters.
  4. Assembling individual items into a final formatted output.
  5. Validating the output so empty/placeholder results are rejected.
  6. Returning the cleaned, validated result.

Why per-item generation for quiz and flashcards?
  FLAN-T5-Small has a 512-token input limit. Asking for "5 Q&A pairs"
  in a single prompt means the context + instruction + all 5 outputs
  must fit in 512 tokens, which causes truncation and garbled output.
  Instead we call the model once per item (5 calls) and assemble the
  results. Each call gets the full 512-token budget for the notes.
"""

import logging
import re
from app.prompts import get_prompt, get_item_prompt, get_task_config
from app.model import generate_text
from app.llm_client import is_groq_available, generate_with_groq

logger = logging.getLogger(__name__)

# Number of items to generate for quiz and flashcards
NUM_ITEMS = 5

# Minimum character length for the assembled output to be considered useful.
MIN_OUTPUT_CHARS = {
    "summary": 80,    # Two-call strategy always produces more than 80 chars
    "key_points": 100,  # Five numbered lines always exceed 100 chars
    "quiz": 80,
    "flashcards": 80,
}


def _clean_text(text: str) -> str:
    """Strip leading/trailing whitespace and collapse multiple blank lines."""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _is_garbage(text: str) -> bool:
    """
    Return True if the generated text is clearly garbage/placeholder.
    Detects only very specific unfilled template tokens, not real content.
    """
    stripped = text.strip()
    if not stripped:
        return True
    # Catch the specific "[question]" / "[answer]" / "[term]" literal echoes
    garbage_patterns = [
        r"^\[question\]",
        r"^\[answer\]",
        r"^\[term\]",
        r"^\[concept\]",
        r"^\[definition\]",
    ]
    for pat in garbage_patterns:
        if re.match(pat, stripped, flags=re.IGNORECASE):
            return True
    return False


def _split_numbered_list(text: str) -> str:
    """
    Split a numbered list that the model packed onto a single line.

    FLAN-T5-Small often outputs "1. X 2. Y 3. Z" without line breaks.
    We insert a newline before each "N." pattern so the frontend can
    render them as separate bullet items.

    Example:
        "1. Photosynthesis... 2. Chloroplasts... 3. ATP..."
        →  "1. Photosynthesis...\n2. Chloroplasts...\n3. ATP..."
    """
    # Insert a newline before "2." "3." ... "9." when preceded by text
    result = re.sub(r"(?<=[a-zA-Z0-9,\.\)])\s+([2-9]\.\s)", r"\n\1", text)
    return result


def _clean_summary(text: str) -> str:
    """
    Post-process a raw summary string:
      - Remove common prefixes the model adds (\"Note:\", \"Summary:\")
      - Strip list markers (\"1. \", \"- \", \"• \") that bleed in from structured notes
      - Collapse multiple spaces
    """
    # Strip leading label echoes
    text = re.sub(r"^(Note|Summary|Overview)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
    # Strip list markers at the start of any sentence
    text = re.sub(r"(?m)^\d+[\.\)]\s+", "", text)
    text = re.sub(r"(?m)^[-•]\s+", "", text)
    # Collapse runs of whitespace / multiple spaces
    text = re.sub(r"  +", " ", text)
    return text.strip()


def _combine_summary_parts(part1: str, part2: str) -> str:
    """
    Join two summary paragraphs into one coherent paragraph.

    Handles:
    - Deduplication (part2 largely repeating part1)
    - Ensuring part1 ends with punctuation
    - Stripping list artifacts from part2
    """
    part1 = _clean_summary(part1)
    part2 = _clean_summary(part2)

    if not part2 or _is_garbage(part2) or len(part2) < 20:
        return part1

    # Skip part2 if it substantially overlaps part1 (first 60 chars match)
    overlap_probe = part2[:60].lower().strip()
    if overlap_probe and overlap_probe in part1.lower():
        logger.info("[services.py] Summary part2 is a duplicate of part1 — skipping.")
        return part1

    # Ensure part1 ends with sentence-ending punctuation
    if part1 and part1[-1] not in ".!?":
        part1 = part1 + "."

    return f"{part1} {part2}"


def _generate_summary(text: str) -> str:
    """
    Generate a coherent summary using TWO complementary model calls.

    Why two calls?
    --------------
    Diagnostic testing showed FLAN-T5-Small stops after the first complete
    thought (definition + equation, ~232 chars). A single prompt cannot
    cover both the overview AND the stages/factors within the 512-token limit.

    Call 1 — OVERVIEW (SUMMARY_PROMPT):
        Prompt D from diagnostics — best at producing the main definition
        and equation. Output: "X is the process by which... The equation is..."

    Call 2 — DETAILS (SUMMARY_DETAIL_PROMPT):
        Asks specifically for stages, components, factors. Covers the content
        the overview misses.

    The two outputs are joined by _combine_summary_parts(), which deduplicates
    and ensures clean punctuation between the two halves.

    Args:
        text: Validated study notes.

    Returns:
        Combined, cleaned summary paragraph.
    """
    from app.prompts import SUMMARY_DETAIL_PROMPT

    # ── Call 1: Overview / definition ────────────────────────────────────────
    prompt1 = get_prompt(task="summary", text=text)
    raw1 = generate_text(prompt1, task="summary").strip()
    logger.info(f"[services.py] Summary call 1 ({len(raw1)} chars): {raw1[:100]}")

    # ── Call 2: Stages / components / factors ─────────────────────────────────
    prompt2 = SUMMARY_DETAIL_PROMPT.format(text=text.strip())
    raw2 = generate_text(prompt2, task="summary").strip()
    logger.info(f"[services.py] Summary call 2 ({len(raw2)} chars): {raw2[:100]}")

    combined = _combine_summary_parts(raw1, raw2)
    return _clean_text(combined)


def _is_merged_point(text: str) -> bool:
    """
    Return True if a single key-point looks like multiple merged concepts.
    Heuristics: contains embedded list markers or is very long (paragraph-length).
    Also catches trailing '... 1.' '... 2.' artifacts from chunked list extraction.
    Does NOT flag O(n log n), O(n²) etc. as list markers.
    """
    stripped = text.strip()
    # Embedded numbered list: "N. " where N is NOT preceded by '(' (to avoid O(n²))
    if re.search(r'(?<!\()\s\d+\.(?:\s|$)', stripped):
        return True
    # Embedded dash-list items: " - Capital"
    if re.search(r'\s-\s[A-Z]', stripped):
        return True
    # Multiple colon-separated clause labels (e.g. "Insertion Sort: ... Stability: ...")
    # Count colons that are NOT inside parentheses
    colon_count = len(re.findall(r'(?<!\()[A-Za-z][^()]*:', stripped))
    if colon_count >= 2:
        return True
    # Paragraph-length — not a bullet
    if len(stripped) > 180:
        return True
    return False


def _chunk_text(text: str, n: int) -> list:
    """
    Split text into n roughly equal sentence-level chunks.

    Strategy:
    1. Split on sentence boundaries (. ! ?)
    2. Distribute sentences into n groups of roughly equal size
    3. Each chunk is passed to a separate model call as its own mini-passage

    This ensures each model call sees DIFFERENT content → different output.
    """
    # Split into sentences, keeping punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    if len(sentences) == 0:
        return [text]

    # Each chunk needs at least 2 sentences so the model has real context.
    # Distribute sentences into n groups, minimum 2 sentences per group.
    chunks = []
    group_size = max(2, len(sentences) // n)
    for i in range(n):
        start = i * group_size
        end = start + group_size if i < n - 1 else len(sentences)
        chunk = " ".join(sentences[start:end]).strip()
        if chunk and len(chunk) > 40:
            chunks.append(chunk)

    return chunks if chunks else [text]


def _clean_key_point(text: str) -> str:
    """
    Strip model-injected prefixes and artifacts from a single key point.

    Handles:
    - Echo of the 'summarize:' or 'summary:' prompt prefix
    - Leading number echoes like '1. ' '2. ' at the start
    - Section-header artifacts ending with ':'
    """
    t = text.strip()
    # Strip leading 'summarize:' / 'summary:' echo
    t = re.sub(r'^(summarize|summary)\s*:\s*', '', t, flags=re.IGNORECASE).strip()
    # Strip leading numbering echo '1. ' '2.' etc.
    t = re.sub(r'^\d+[\.):]\s*', '', t).strip()
    # Strip again in case of double prefix like '1. summarize:'
    t = re.sub(r'^(summarize|summary)\s*:\s*', '', t, flags=re.IGNORECASE).strip()
    return t


def _generate_key_points(text: str) -> str:
    """
    Generate key points by summarising SHORT SECTIONS of the notes.

    Final approach after exhaustive diagnostic testing:
    ─────────────────────────────────────────────────
    Every prompting strategy that passes the FULL notes (topic hints,
    POINT N: format, QA, chunk extraction) produces the same output because
    FLAN-T5-Small always picks its single highest-confidence token sequence
    regardless of the instruction. The model ignores aspect hints entirely.

    The ONLY thing that changes model output is changing the INPUT TEXT.

    Fix: Split notes into short sections of ~2-3 sentences each. For each
    section, run "summarize:" which is FLAN-T5's native training prefix for
    producing one concise sentence from a short passage. Different input →
    naturally different output. No topic hints needed.

    Validation: accept ≥ 2 unique points (not 3) since very short notes
    may only yield a few meaningful sections. Display what we have rather
    than throwing an error for borderline inputs.

    Args:
        text: Validated study notes.

    Returns:
        Newline-separated numbered list: "1. ...\n2. ...\n..."
    """
    # Use FLAN-T5's native summarization prefix — shortest effective prompt
    SECTION_PROMPT = "summarize: {section}"

    text = text.strip()

    # ── Split into short sections (2-3 sentences each) ───────────────────────
    # Strategy: split on sentence boundaries, group into sections of ~2 sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    # If very few sentences, try splitting on newlines or colons instead
    if len(sentences) < 3:
        sentences = [s.strip() for s in re.split(r'\n+', text) if len(s.strip()) > 20]

    if len(sentences) < 2:
        # Last resort: just use the whole text as one section
        sentences = [text]

    # Group into up to 5 sections of ~2 sentences each
    section_size = max(1, min(3, len(sentences) // 5 + 1))
    sections = []
    for i in range(0, len(sentences), section_size):
        section = " ".join(sentences[i:i + section_size]).strip()
        if len(section) > 25:
            sections.append(section)
        if len(sections) >= 5:
            break

    logger.info(f"[services.py] Key points: {len(sections)} sections from {len(sentences)} sentences")

    # ── One model call per section ────────────────────────────────────────────
    points = []
    for i, section in enumerate(sections):
        prompt = SECTION_PROMPT.format(section=section)
        try:
            raw = generate_text(prompt, task="key_points").strip()
            logger.info(f"[services.py] KP section {i+1} ({len(raw)} chars): {raw[:100]}")
        except Exception as exc:
            logger.warning(f"[services.py] KP section {i+1} error: {exc}")
            continue

        if not raw or _is_garbage(raw) or len(raw) < 10:
            continue

        raw = _clean_key_point(raw)
        if not raw or len(raw) < 10:
            continue

        # Skip section headers (e.g. "Light-independent reactions:")
        if raw.rstrip().endswith(':'):
            logger.info(f"[services.py] KP section {i+1} is a header — skipped")
            continue

        if _is_merged_point(raw):
            logger.info(f"[services.py] KP section {i+1} merged — skipped")
            continue

        # Reject word-soup: high repetition in short output
        words = raw.lower().split()
        if len(words) <= 10 and len(set(words)) < len(words) * 0.6:
            logger.info(f"[services.py] KP section {i+1} repetitive — skipped")
            continue

        # Deduplicate on first 45 chars
        probe = raw[:45].lower().strip()
        if any(probe in p.lower() for p in points):
            logger.info(f"[services.py] KP section {i+1} duplicate — skipped")
            continue

        points.append(raw.rstrip(".").strip() + ".")

    if len(points) < 2:
        raise ValueError(
            f"Key points generation produced only {len(points)} valid unique "
            "point(s). Please try again with more detailed notes (at least 3-4 sentences)."
        )

    final = points[:5]
    return "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(final))





def _generate_quiz(text: str) -> str:
    """
    Generate 5 Q&A pairs by calling the model once per question.

    Returns:
        Formatted string with all Q&A pairs.
    """
    pairs = []
    for i in range(NUM_ITEMS):
        prompt = get_item_prompt(task="quiz", text=text, item_index=i)
        try:
            raw = generate_text(prompt, task="quiz")
            raw = raw.strip()
            logger.info(f"[services.py] Quiz item {i+1} raw: {raw[:80]}")

            if _is_garbage(raw) or len(raw) < 10:
                logger.warning(f"[services.py] Quiz item {i+1} discarded (garbage).")
                continue

            # The prompt ends with "Question:" so the model outputs the question.
            # We then need the answer — check if the model already included it.
            if "\nAnswer:" in raw or "\nanswer:" in raw:
                # Model included both question and answer
                question_part = re.split(r"\n[Aa]nswer:", raw)[0].strip()
                answer_part = re.split(r"\n[Aa]nswer:", raw)[1].strip() if len(re.split(r"\n[Aa]nswer:", raw)) > 1 else ""
            else:
                question_part = raw
                answer_part = ""

            # If no answer was generated, run a second call to get the answer
            if not answer_part:
                answer_prompt = (
                    f"Answer the following question based on the text.\n\n"
                    f"Text: {text.strip()}\n\n"
                    f"Question: {question_part}\n\nAnswer:"
                )
                answer_raw = generate_text(answer_prompt, task="quiz")
                answer_part = answer_raw.strip()

            if question_part and answer_part and not _is_garbage(answer_part):
                pairs.append(f"Q{i+1}: {question_part}\nA{i+1}: {answer_part}")
            elif question_part:
                pairs.append(f"Q{i+1}: {question_part}\nA{i+1}: (see notes)")

        except Exception as e:
            logger.warning(f"[services.py] Quiz item {i+1} failed: {e}")
            continue

    return "\n\n".join(pairs)


def _generate_flashcards(text: str) -> str:
    """
    Generate 5 flashcards by calling the model once per card.

    The flashcard prompt now uses Question:/Answer: format (which FLAN-T5
    handles better than Term:/Definition:). We then re-label the output
    as Front:/Back: so the frontend can render them as flashcards.

    Returns:
        Formatted string with all flashcards (Front:/Back: format).
    """
    cards = []
    for i in range(NUM_ITEMS):
        prompt = get_item_prompt(task="flashcards", text=text, item_index=i)
        try:
            raw = generate_text(prompt, task="flashcards")
            raw = raw.strip()
            logger.info(f"[services.py] Flashcard item {i+1} raw: {raw[:80]}")

            if _is_garbage(raw) or len(raw) < 5:
                logger.warning(f"[services.py] Flashcard {i+1} discarded (garbage).")
                continue

            # The prompt ends with "Question:" so the model outputs the question.
            # Parse Question/Answer — same logic as quiz generation.
            if "\nAnswer:" in raw or "\nanswer:" in raw:
                question_part = re.split(r"\n[Aa]nswer:", raw)[0].strip()
                answer_part = re.split(r"\n[Aa]nswer:", raw)[1].strip()
            else:
                question_part = raw
                answer_part = ""

            # If no answer was generated, run a second call
            if not answer_part:
                answer_prompt = (
                    f"Answer the following question based on the text.\n\n"
                    f"Text: {text.strip()}\n\n"
                    f"Question: {question_part}\n\nAnswer:"
                )
                answer_raw = generate_text(answer_prompt, task="flashcards")
                answer_part = answer_raw.strip()

            # Re-label as Front:/Back: for the frontend
            if question_part and answer_part and not _is_garbage(answer_part):
                cards.append(f"Front: {question_part}\nBack: {answer_part}")
            elif question_part:
                cards.append(f"Front: {question_part}\nBack: (see notes)")

        except Exception as e:
            logger.warning(f"[services.py] Flashcard {i+1} failed: {e}")
            continue

    return "\n\n".join(cards)


def _validate_output(result: str, task: str) -> None:
    """
    Raise ValueError if the generated output is empty or too short.

    Args:
        result: The assembled output string.
        task:   The task that was requested.

    Raises:
        ValueError: If the output fails validation.
    """
    stripped = result.strip()

    if not stripped:
        raise ValueError(f"Model returned an empty response for task '{task}'.")

    min_chars = MIN_OUTPUT_CHARS.get(task, 30)
    if len(stripped) < min_chars:
        raise ValueError(
            f"Model output is too short ({len(stripped)} chars) for task '{task}'. "
            f"Minimum expected: {min_chars} chars. Raw output: {stripped!r}"
        )


def process_request(text: str, task: str) -> tuple[str, str]:
    """
    Handle a study-material generation request.

    Primary Engine: Groq Cloud API (fast LPU inference, rich output).
    Fallback Engine: Local FLAN-T5-Small model (CPU inference).

    Args:
        text:  Validated student notes.
        task:  One of "summary", "key_points", "quiz", "flashcards".

    Returns:
        tuple of (result_text, model_used_name)

    Raises:
        ValueError:   If the task is not recognised or output validation fails.
        RuntimeError: If the model is not loaded.
        Exception:    For any unexpected model/generation error.
    """
    logger.info(f"[services.py] Processing task='{task}', text_length={len(text)}")

    # ── 1. Primary: Try Groq API ──
    if is_groq_available():
        try:
            logger.info("[services.py] Attempting primary engine: Groq API...")
            result = generate_with_groq(text=text, task=task)
            _validate_output(result, task)
            logger.info(f"[services.py] Groq generation succeeded ({len(result)} chars).")
            return result, "Groq (Llama 3.3 70B)"
        except Exception as e:
            logger.warning(
                f"[services.py] Groq generation failed: {e}. Falling back to local model...",
                exc_info=True,
            )

    # ── 2. Fallback: Local FLAN-T5-Small model ──
    logger.info("[services.py] Running local FLAN-T5-Small model inference...")
    if task == "summary":
        result = _generate_summary(text)
    elif task == "key_points":
        result = _generate_key_points(text)
    elif task == "quiz":
        result = _generate_quiz(text)
    elif task == "flashcards":
        result = _generate_flashcards(text)
    else:
        raise ValueError(
            f"Unknown task: '{task}'. "
            f"Valid tasks: summary, key_points, quiz, flashcards"
        )

    logger.info(
        f"[services.py] Local generation complete. Output length: {len(result)} chars"
    )
    logger.debug(f"[services.py] Output:\n{result[:400]}")

    # Validate the assembled output before returning
    _validate_output(result, task)

    return result, "Local (FLAN-T5-Small)"
