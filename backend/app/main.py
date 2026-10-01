"""
main.py
-------
FastAPI application entry point.

Responsibilities:
  - Load the FLAN-T5-Small model once at application startup.
  - Configure CORS to allow requests from the React development server.
  - Expose the /generate endpoint.
  - Expose a /health endpoint for status checks.
  - Return friendly error messages (never raw Python stack traces).
"""

import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.model import load_model, is_model_loaded
from app.llm_client import is_groq_available
from app.schemas import GenerateRequest, GenerateResponse, HealthResponse
from app.services import process_request

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Lifespan — runs once at startup and shutdown
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    On startup:  Load the FLAN-T5-Small model into RAM (CPU).
    On shutdown: Nothing extra needed — Python GC handles cleanup.

    The model is loaded ONCE and reused for every request.
    This is critical for keeping memory stable on an 8 GB laptop.
    """
    logger.info("=" * 60)
    logger.info("  Smart Notes Condenser — Backend Starting")
    logger.info("=" * 60)
    logger.info("Loading FLAN-T5-Small... (this may take 30-60 seconds on first run)")
    load_model()
    logger.info("Model ready. Server is accepting requests.")
    yield
    # Shutdown
    logger.info("Server shutting down.")


# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title="Smart Notes Condenser API",
    description=(
        "Converts student study notes into concise study material using "
        "a pretrained FLAN-T5-Small Transformer model running on CPU. "
        "No external API keys required — all inference is performed locally."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# CORS — allow React dev server
# ─────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """
    Health check endpoint.
    Returns whether the server is running, whether the local model is loaded,
    and whether Groq API is available.
    """
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        groq_available=is_groq_available(),
    )


@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate(request: GenerateRequest):
    """
    Main generation endpoint.

    Accepts student notes and a task type, then returns the AI-generated
    study material using Groq (primary) or local FLAN-T5 (fallback).

    Request body:
        text (str):  Student notes
        task (str):  "summary" | "key_points" | "quiz" | "flashcards"

    Response:
        result (str): Generated study material
        model_used (str): Engine used for generation
    """
    try:
        result, model_used = process_request(text=request.text, task=request.task)
        return GenerateResponse(result=result, model_used=model_used)

    except ValueError as e:
        # Invalid task or prompt error — user-facing
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # Model not loaded or device error
        logger.error(f"[main.py] RuntimeError during generation: {e}")
        raise HTTPException(status_code=503, detail="Model is unavailable. Please restart the server.")

    except Exception as e:
        # Catch-all — log the real error but return a friendly message
        logger.error(f"[main.py] Unexpected error during generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during generation. Please try again with shorter or different input.",
        )
