"""
llm_client.py
-------------
Groq Cloud API integration using state-of-the-art models (e.g. Llama 3.3 70B).
Provides high-speed (<1s) and high-quality generation of summaries, key points,
quizzes, and flashcards.
"""

import logging
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Primary model for Groq
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_groq_client = None


def get_groq_client():
    """Lazily instantiate and return the Groq client."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            return None
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def is_groq_available() -> bool:
    """Check if Groq API key is configured."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    return bool(api_key and not api_key.startswith("your_"))


SYSTEM_PROMPT = (
    "You are an expert academic tutor and AI study assistant. "
    "Your goal is to transform student study notes into clear, high-quality, "
    "accurate, and comprehensive study materials. Adhere strictly to the requested format."
)

TASK_PROMPTS = {
    "summary": """Write a comprehensive, clear, and well-structured abstractive summary of the study notes below.
Capture the main definitions, key mechanisms/processes, and critical details in a cohesive 1-2 paragraph format.

Notes:
{text}

Summary:""",

    "key_points": """Extract the 5 most essential key points from the study notes below.
Format your output EXACTLY as a numbered list from 1 to 5.
Each point should be a complete, informative sentence highlighting a distinct core concept.

Notes:
{text}

Key Points:
1. """,

    "quiz": """Create 5 high-yield study/exam questions with accurate answers based strictly on the study notes below.
Format each item EXACTLY like this:
Q1: [Question text]
A1: [Concise and accurate answer]

Q2: [Question text]
A2: [Concise and accurate answer]

Q3: [Question text]
A3: [Concise and accurate answer]

Q4: [Question text]
A4: [Concise and accurate answer]

Q5: [Question text]
A5: [Concise and accurate answer]

Notes:
{text}""",

    "flashcards": """Create 5 active-recall flashcards based strictly on the study notes below.
Each card must test a core concept, key term, mechanism, or principle.
Format each item EXACTLY like this:
Front: [Concept, term, or question]
Back: [Clear, concise definition or answer]

Front: [Concept, term, or question]
Back: [Clear, concise definition or answer]

Notes:
{text}"""
}


# Primary and fallback models for Groq
CANDIDATE_MODELS = [
    os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
]


import random

QUIZ_FOCUS_ANGLES = [
    "Focus on deep conceptual understanding, mechanisms, and cause-and-effect relationships.",
    "Focus on specific terminology, definitions, chemical formulas/equations, and exact components.",
    "Focus on inputs/outputs, environmental conditions, limiting factors, and distinctions.",
    "Focus on step-by-step phases, organelles/structures involved, and practical implications.",
    "Focus on the 'why' and 'how' behind key steps and the specific role of critical elements.",
]

FLASHCARD_FOCUS_ANGLES = [
    "Focus on core definitions and primary terminology.",
    "Focus on specific functions, structures, and stages.",
    "Focus on key formulas, numerical factors, and essential conditions.",
]


def _build_task_prompt(task: str, text: str) -> str:
    """Build task-specific prompt with dynamic focus rotation for quiz and flashcards."""
    text = text.strip()

    if task == "summary":
        return TASK_PROMPTS["summary"].format(text=text)

    elif task == "key_points":
        return TASK_PROMPTS["key_points"].format(text=text)

    elif task == "quiz":
        angle = random.choice(QUIZ_FOCUS_ANGLES)
        nonce = random.randint(1000, 9999)
        return (
            f"Create a fresh, unique set of 5 distinct high-yield study/exam questions with accurate answers "
            f"based STRICTLY on the study notes below.\n"
            f"Special focus for this set ({nonce}): {angle}\n"
            f"Make sure every question tests a different detail or angle from the text and avoid repeating common generic questions.\n\n"
            f"Format each item EXACTLY like this:\n"
            f"Q1: [Question text]\n"
            f"A1: [Concise and accurate answer]\n\n"
            f"Q2: [Question text]\n"
            f"A2: [Concise and accurate answer]\n\n"
            f"Q3: [Question text]\n"
            f"A3: [Concise and accurate answer]\n\n"
            f"Q4: [Question text]\n"
            f"A4: [Concise and accurate answer]\n\n"
            f"Q5: [Question text]\n"
            f"A5: [Concise and accurate answer]\n\n"
            f"Notes:\n{text}"
        )

    elif task == "flashcards":
        angle = random.choice(FLASHCARD_FOCUS_ANGLES)
        nonce = random.randint(1000, 9999)
        return (
            f"Create 5 unique active-recall flashcards based strictly on the study notes below.\n"
            f"Special focus ({nonce}): {angle}\n"
            f"Each card must test a distinct core concept, key term, mechanism, or principle.\n\n"
            f"Format each item EXACTLY like this:\n"
            f"Front: [Concept, term, or question]\n"
            f"Back: [Clear, concise definition or answer]\n\n"
            f"Front: [Concept, term, or question]\n"
            f"Back: [Clear, concise definition or answer]\n\n"
            f"Notes:\n{text}"
        )

    raise ValueError(f"Unsupported task: '{task}'")


def generate_with_groq(text: str, task: str) -> str:
    """
    Generate study material using Groq Cloud API.

    Args:
        text: Student notes text.
        task: "summary" | "key_points" | "quiz" | "flashcards"

    Returns:
        Generated text string matching the frontend renderer format.

    Raises:
        RuntimeError / Exception: If Groq API call fails or client is unavailable.
    """
    client = get_groq_client()
    if client is None:
        raise RuntimeError("Groq API client is not configured or GROQ_API_KEY is missing.")

    user_prompt = _build_task_prompt(task, text)

    # Use higher temperature for quiz/flashcards to generate fresh variety each time
    temperature = 0.85 if task in ["quiz", "flashcards"] else 0.3

    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            logger.info(f"[llm_client.py] Calling Groq API ({model_name}) for task='{task}' with temp={temperature}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1024,
            )

            result = response.choices[0].message.content.strip()

            # For key_points, ensure line 1 numbering is preserved if template seeded it
            if task == "key_points" and not result.startswith("1."):
                result = "1. " + result

            logger.info(f"[llm_client.py] Groq generation successful with {model_name} ({len(result)} chars).")
            return result
        except Exception as err:
            logger.warning(f"[llm_client.py] Model {model_name} failed: {err}")
            last_error = err
            continue

    raise last_error or RuntimeError("All Groq candidate models failed.")
