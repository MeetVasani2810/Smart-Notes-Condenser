"""
model.py
--------
Loads the FLAN-T5-Small pretrained Transformer model and exposes a
task-aware text generation function.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEEP LEARNING EXPLANATION (for college presentation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What is FLAN-T5-Small?
  - A pretrained Transformer-based encoder-decoder neural network.
  - Developed by Google.
  - "FLAN" = Fine-tuned LAnguage Net — trained on 1800+ NLP tasks with
    natural language instructions.
  - "T5" = Text-To-Text Transfer Transformer — treats every NLP task as a
    text-to-text problem.
  - "Small" = the smallest variant (~80M parameters), suitable for CPU inference.

What is inference?
  - We are NOT training the model. We are using its already-learned weights
    to generate output for new input. This is called "inference".

What is tokenization?
  - The model cannot read raw text. The tokenizer converts text into
    integer token IDs that the model understands.
  - After generation, the tokenizer converts the output token IDs back to text.

Why torch.no_grad()?
  - During training, PyTorch tracks gradients (derivatives) to update model
    weights. During inference, we do not need gradients.
  - torch.no_grad() disables gradient tracking, saving memory and making
    inference faster.

Why model.eval()?
  - Some model components (like Dropout and BatchNorm) behave differently
    during training vs inference. model.eval() puts the model into
    inference mode, ensuring correct and consistent behaviour.

Why per-task generation parameters?
  - Different tasks need different output lengths and quality trade-offs.
  - Summaries need fewer tokens; quiz/flashcards need more.
  - length_penalty > 1.0 encourages the model to produce longer, more
    complete answers instead of stopping early.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
MODEL_NAME = "google/flan-t5-small"

# Maximum number of tokens the model receives as input.
# 512 is the model's native maximum; we keep it at 512 to use the full context.
MAX_INPUT_TOKENS = 512

# ─────────────────────────────────────────────
# Module-level state (loaded once at startup)
# ─────────────────────────────────────────────
_tokenizer = None
_model = None
_device = None


def load_model() -> None:
    """
    Load the FLAN-T5-Small tokenizer and model into memory.

    This function is called ONCE when the FastAPI application starts.
    The model is never reloaded between requests — this is critical for
    keeping RAM usage stable on an 8 GB laptop.

    Device selection:
      - If a CUDA GPU is available, use it.
      - Otherwise, fall back to CPU (expected on most laptops).
    """
    global _tokenizer, _model, _device

    # Determine compute device
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"[model.py] Using device: {_device}")

    logger.info(f"[model.py] Loading tokenizer for '{MODEL_NAME}'...")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    logger.info(f"[model.py] Loading model '{MODEL_NAME}'...")
    _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    # Move model to selected device (CPU in most cases)
    _model = _model.to(_device)

    # Put model into evaluation/inference mode.
    # This disables Dropout layers and ensures BatchNorm uses running statistics.
    _model.eval()

    logger.info("[model.py] Model loaded and ready for inference.")


def is_model_loaded() -> bool:
    """Return True if the model has been loaded successfully."""
    return _model is not None and _tokenizer is not None


def generate_text(prompt: str, task: str = "summary") -> str:
    """
    Run task-aware inference on the loaded FLAN-T5-Small model.

    Flow:
      1. Look up per-task generation parameters (max tokens, beams, etc.)
      2. Tokenize the prompt (text → token IDs)
      3. Pass token IDs through the encoder-decoder Transformer
      4. Decode the output token IDs back to text
      5. Re-attach the prompt seed (for tasks whose prompt ends mid-output)

    Args:
        prompt: The formatted instruction prompt string.
        task:   One of "summary", "key_points", "quiz", "flashcards".
                Used to select appropriate generation parameters.

    Returns:
        Generated text string (decoded model output).

    Raises:
        RuntimeError: If the model has not been loaded yet.
    """
    if not is_model_loaded():
        raise RuntimeError("Model is not loaded. Call load_model() first.")

    # Import here to avoid circular imports at module level
    from app.prompts import get_task_config
    task_cfg = get_task_config(task)

    # ── Step 1: Tokenization ──────────────────────────────────────────────────
    # Convert the text prompt into a tensor of integer token IDs.
    # truncation=True ensures we never exceed MAX_INPUT_TOKENS even if the
    # user somehow bypasses the character limit check.
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",       # Return PyTorch tensors
        max_length=MAX_INPUT_TOKENS,
        truncation=True,
    )

    # Move input tensors to the same device as the model
    input_ids = inputs["input_ids"].to(_device)
    attention_mask = inputs["attention_mask"].to(_device)

    logger.info(
        f"[model.py] Task='{task}' | input_tokens={input_ids.shape[1]} "
        f"| max_new_tokens={task_cfg['max_new_tokens']} | num_beams={task_cfg['num_beams']}"
    )

    # ── Step 2: Model Inference ───────────────────────────────────────────────
    # torch.no_grad() disables gradient computation.
    # This is essential during inference: saves memory and speeds up generation.
    with torch.no_grad():
        output_ids = _model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=task_cfg["max_new_tokens"],
            num_beams=task_cfg["num_beams"],
            length_penalty=task_cfg["length_penalty"],
            min_length=task_cfg["min_length"],
            no_repeat_ngram_size=task_cfg["no_repeat_ngram_size"],
            do_sample=False,       # Deterministic beam search
            early_stopping=True,  # Stop when all beams hit EOS
        )

    # ── Step 3: Decoding ─────────────────────────────────────────────────────
    # Convert the output token IDs back into a human-readable string.
    # skip_special_tokens=True removes padding and end-of-sequence tokens.
    generated_text = _tokenizer.decode(
        output_ids[0],
        skip_special_tokens=True,
    )

    raw = generated_text.strip()
    logger.info(f"[model.py] Raw output ({len(raw)} chars): {raw[:120]}...")

    return raw
