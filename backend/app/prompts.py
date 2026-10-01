"""
prompts.py
----------
Prompt templates for each NLP task, optimised for FLAN-T5-Small.

FLAN-T5-Small is an instruction-tuned model trained on 1800+ NLP tasks.
At only 80M parameters with a 512-token input limit, it works best with:
  - Very short, focused prompts (no multi-example few-shot preambles)
  - Native FLAN-T5 task formats ("summarize:", "generate question:", etc.)
  - One output item per call for structured tasks (quiz/flashcards)

Key insight: Long few-shot examples eat into the 512-token budget, leaving
little room for the actual user content. Keep prompts minimal.
"""

# ─────────────────────────────────────────────
# Abstractive Text Summarization — two-call strategy
# ─────────────────────────────────────────────
# Diagnostic testing (Phase 1 & 2) showed:
#   - Variant A ("in 4 to 6 sentences"): only 149 chars, disconnected
#   - Variant B (native "summarize:"): 144 chars + hallucinations
#   - Variant D (direct "main topic + key concepts"): best start (232 chars)
#     but model stops after the equation — never reaches stages/factors.
#   - length_penalty > 1.5 causes hallucinated equations ("6C2+5C2/6C3...")
#
# Solution: run TWO focused calls and join them.
#   Call 1 — OVERVIEW: produces the definition + main equation (232 chars)
#   Call 2 — DETAILS:  produces stages, components, factors (separate content)
# services._generate_summary() combines them into one coherent paragraph.

SUMMARY_PROMPT = """Write a summary of the following notes. Cover the main topic, key concepts, and important details in one paragraph.

Notes:
{text}

Summary:"""

# Second call: targets the parts the overview misses (stages, steps, factors)
SUMMARY_DETAIL_PROMPT = """Based on the following notes, describe in 2 sentences the key stages, components, or processes involved and any important factors or conditions mentioned.

Notes:
{text}

Key stages and details:"""


# ─────────────────────────────────────────────
# Key Information Extraction — per-item strategy
# ─────────────────────────────────────────────
# Diagnostic (Phase 1-3) proved a single call CANNOT reliably extract 5
# separate points from FLAN-T5-Small:
#   - Single numbered-list prompt: merges everything into 1-2 bloated points
#   - "POINT N:" format:          echoes the [placeholder], dumps everything
#   - Generic per-item hint:       repeats the same sentence for all 5 calls
#
# Solution: 5 separate calls, each with a NARROW, ATOMIC topic hint that
# forces the model to extract a DIFFERENT piece of information per call.
# Same strategy that works for quiz/flashcards.
#
# Critical constraint: the prompt must be short enough that the notes fit
# within the 512-token input limit.
KEY_POINT_ITEM_PROMPT = """Based on the notes below, write one key fact about {topic} as a single complete sentence.

Notes:
{text}

Key fact:"""

# Five rotating topic hints that cover different aspects of any subject.
# These are intentionally generic so they work for biology, physics, CS, etc.
KEY_POINT_TOPICS = [
    "what the main concept is or what it does",
    "the first main stage, step, or process described",
    "the second main stage, component, or equation described",
    "a specific mechanism, tool, or important term mentioned",
    "a key factor, condition, or application mentioned",
]

# Kept for PROMPT_TEMPLATES dict — not used for generation any more.
# services.py routes key_points through _generate_key_points() instead.
KEY_POINTS_PROMPT = KEY_POINT_ITEM_PROMPT  # backward-compat alias


# ─────────────────────────────────────────────
# Question Generation (Quiz) — single item
# ─────────────────────────────────────────────
# FLAN-T5 was fine-tuned on "generate question" tasks.
# We generate one Q&A per call and loop in services.py.
# The "topic hint" parameter helps focus each question.
QUIZ_ITEM_PROMPT = """Based on the text below, write one exam question and its answer about {topic}.

Text: {text}

Question:"""


# ─────────────────────────────────────────────
# Flashcard Generation — single item
# ─────────────────────────────────────────────
# We generate one flashcard per call and loop in services.py.
# Using Question:/Answer: format rather than Term:/Definition: because
# FLAN-T5 was fine-tuned heavily on Q&A tasks and generates much better
# answers in that format. Services.py re-labels these as Front:/Back:.
FLASHCARD_ITEM_PROMPT = """Based on the text below, write one study question about {topic} and give the answer.

Text: {text}

Question:"""


# ─────────────────────────────────────────────
# Topic hints for quiz and flashcard generation
# ─────────────────────────────────────────────
# These rotate across calls so each generated item covers a different aspect.
QUIZ_TOPICS = [
    "the main definition or core concept",
    "a key stage, step, or phase",
    "an important equation, formula, or chemical reaction",
    "factors, environmental conditions, or variables that affect the process",
    "a specific mechanism, structure, or organelle involved",
    "the role of specific enzymes, catalysts, or essential components",
    "inputs, outputs, and byproducts generated",
    "why this process is biologically or conceptually significant",
]

FLASHCARD_TOPICS = [
    "the definition of the main concept",
    "the first main stage or step",
    "the second main stage or step",
    "an important equation, formula, or key term",
    "a key factor that affects the process",
    "a specific structure, enzyme, or component",
    "the primary product or outcome",
]


# ─────────────────────────────────────────────
# Per-task generation configuration
# ─────────────────────────────────────────────
TASK_CONFIG = {
    "summary": {
        # Validated via grid search (Phase 2 diagnostics):
        # P1 (160 tokens, LP=1.2, min=40) gives the best coherent output.
        # Higher LP (>=1.5) causes hallucinated equations; beam=2 skips the definition.
        # Two calls are made for summary — these params apply to BOTH calls.
        "max_new_tokens": 160,
        "num_beams": 4,
        "length_penalty": 1.2,
        "min_length": 40,
        "no_repeat_ngram_size": 3,
    },
    "key_points": {
        # Per-item generation: each call extracts ONE fact (see _generate_key_points).
        # Small max_new_tokens because we only want 1 short sentence per call.
        # LP=1.2 avoids premature EOS without forcing hallucinated extra content.
        "max_new_tokens": 80,
        "num_beams": 4,
        "length_penalty": 1.2,
        "min_length": 8,
        "no_repeat_ngram_size": 3,
    },
    # For quiz and flashcards, these params apply to each individual item call
    "quiz": {
        "max_new_tokens": 100,
        "num_beams": 4,
        "length_penalty": 1.2,
        "min_length": 15,
        "no_repeat_ngram_size": 2,
    },
    "flashcards": {
        "max_new_tokens": 80,
        "num_beams": 4,
        "length_penalty": 1.2,
        "min_length": 10,
        "no_repeat_ngram_size": 2,
    },
}

# ─────────────────────────────────────────────
# Prompt selector (for summary and key_points)
# ─────────────────────────────────────────────
PROMPT_TEMPLATES = {
    "summary": SUMMARY_PROMPT,
    "key_points": KEY_POINTS_PROMPT,
}

# Exported for use in services._generate_summary()
__all__ = [
    "SUMMARY_PROMPT", "SUMMARY_DETAIL_PROMPT",
    "KEY_POINT_ITEM_PROMPT", "KEY_POINT_TOPICS", "KEY_POINTS_PROMPT",
    "QUIZ_ITEM_PROMPT", "FLASHCARD_ITEM_PROMPT",
    "get_prompt", "get_item_prompt", "get_task_config",
]


def get_prompt(task: str, text: str) -> str:
    """
    Build the final prompt string for summary or key_points tasks.

    Args:
        task:  One of "summary", "key_points"
        text:  The student's study notes (already validated)

    Returns:
        Formatted prompt string ready to be tokenized and passed to the model.
    """
    template = PROMPT_TEMPLATES.get(task)
    if template is None:
        raise ValueError(
            f"Unknown task for get_prompt: '{task}'. "
            f"For quiz/flashcards use get_item_prompt()."
        )
    return template.format(text=text.strip())


def get_item_prompt(task: str, text: str, item_index: int) -> str:
    """
    Build a single-item prompt for quiz or flashcard generation.

    Instead of asking for 5 items at once (which exceeds the model's
    capacity), we call the model once per item with a topic hint that
    rotates across different aspects of the notes.

    Args:
        task:       "quiz" or "flashcards"
        text:       The student's study notes
        item_index: 0-based index (0 to 4) to select the topic hint

    Returns:
        Formatted prompt string for generating one Q&A or one flashcard.
    """
    text = text.strip()
    if task == "quiz":
        topic = QUIZ_TOPICS[item_index % len(QUIZ_TOPICS)]
        return QUIZ_ITEM_PROMPT.format(topic=topic, text=text)
    elif task == "flashcards":
        topic = FLASHCARD_TOPICS[item_index % len(FLASHCARD_TOPICS)]
        return FLASHCARD_ITEM_PROMPT.format(topic=topic, text=text)
    else:
        raise ValueError(f"get_item_prompt does not support task '{task}'.")


def get_task_config(task: str) -> dict:
    """
    Return the generation configuration dictionary for a given task.

    Args:
        task: One of "summary", "key_points", "quiz", "flashcards"

    Returns:
        Dict of generation kwargs to pass to model.generate().
    """
    config = TASK_CONFIG.get(task)
    if config is None:
        raise ValueError(f"Unknown task: '{task}'. Valid tasks: {list(TASK_CONFIG.keys())}")
    return config
