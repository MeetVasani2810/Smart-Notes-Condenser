"""
schemas.py
----------
Pydantic models for request/response validation.

The GenerateRequest schema enforces:
  - Non-empty text
  - Maximum 6000 characters (CPU-friendly input limit)
  - Task must be one of the four supported NLP tasks
"""

from pydantic import BaseModel, field_validator
from typing import Literal

# Supported NLP tasks
VALID_TASKS = ["summary", "key_points", "quiz", "flashcards"]

# Maximum input length (characters)
MAX_INPUT_CHARS = 20000


class GenerateRequest(BaseModel):
    """Request body for the /generate endpoint."""

    text: str
    task: Literal["summary", "key_points", "quiz", "flashcards"]

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Input text cannot be empty.")
        if len(v) > MAX_INPUT_CHARS:
            raise ValueError(
                f"Input text is too long. Maximum allowed is {MAX_INPUT_CHARS} characters. "
                f"You provided {len(v)} characters."
            )
        return v


class GenerateResponse(BaseModel):
    """Response body returned by the /generate endpoint."""

    result: str
    model_used: str = "groq"


class HealthResponse(BaseModel):
    """Simple health check response."""

    status: str
    model_loaded: bool
    groq_available: bool = False
