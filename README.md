# 🧠 Smart Notes Condenser

> **A College-Level Deep Learning + NLP Mini Project**  
> Convert student study notes into concise study material using a pretrained FLAN-T5-Small Transformer model — running entirely on your local CPU.

---

## 1. Project Overview

Smart Notes Condenser is a full-stack AI application that takes a student's study notes and uses **Natural Language Processing (NLP)** and **Deep Learning** to generate:

- 📄 **Summaries** — A concise abstractive summary of the notes
- 🔑 **Key Points** — 5 bullet points highlighting the most important concepts
- ❓ **Quiz** — 5 question-and-answer pairs for self-testing
- 🃏 **Flashcards** — 5 front/back flashcards for active recall

**No cloud API. No GPU required. No model training.**  
Everything runs locally on a standard laptop CPU.

---

## 2. Problem Statement

Students often take lengthy, unstructured notes while studying. Converting these notes into useful study material (summaries, flashcards, quizzes) manually is time-consuming. This application automates that process using a pretrained Transformer model.

---

## 3. Objectives

1. Demonstrate the practical application of Deep Learning (Transformer models) for NLP tasks.
2. Build a full-stack application using modern web technologies (React, FastAPI).
3. Perform local AI inference without requiring cloud services, API keys, or a GPU.
4. Create a student-friendly, easy-to-use interface.

---

## 4. Features

| Feature | Description |
|---|---|
| Abstractive Summarization | Generates a concise summary preserving key ideas |
| Key Points Extraction | Extracts 5 bullet points from the notes |
| Quiz Generation | Creates 5 Q&A pairs for self-testing |
| Flashcard Generation | Creates 5 front/back flashcards |
| Character Counter | Live counter with a 6000-character limit |
| Loading Indicator | Informs the student while CPU inference runs |
| Error Handling | Friendly error messages for all failure cases |
| Copy to Clipboard | One-click copy of generated content |

---

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS + Axios |
| Backend | Python + FastAPI + Uvicorn |
| Deep Learning | PyTorch + Hugging Face Transformers |
| Model | google/flan-t5-small |
| Inference | CPU (no GPU required) |

---

## 6. Architecture

### Application Flow

```
┌─────────────────────────────────────────────┐
│              React Frontend                  │
│   (Vite + Tailwind CSS + Axios)              │
│                                              │
│  User types notes → selects task → clicks   │
│  Generate → Axios POST /generate             │
└──────────────────┬──────────────────────────┘
                   │ HTTP POST /generate
                   ▼
┌─────────────────────────────────────────────┐
│            FastAPI Backend                   │
│   (Python + Uvicorn)                         │
│                                              │
│  1. Receive request                          │
│  2. Validate input (Pydantic)                │
│  3. Select prompt template                   │
│  4. Call generate_text()                     │
└──────────────────┬──────────────────────────┘
                   │ Python function call
                   ▼
┌─────────────────────────────────────────────┐
│          FLAN-T5-Small (PyTorch)             │
│   (Loaded once at startup, CPU inference)    │
│                                              │
│  1. Tokenize prompt (text → token IDs)       │
│  2. Encoder processes input tokens           │
│  3. Decoder generates output tokens          │
│  4. Decode output (token IDs → text)         │
└──────────────────┬──────────────────────────┘
                   │ Generated text
                   ▼
┌─────────────────────────────────────────────┐
│              React Frontend                  │
│   Displays result in ResultCard component    │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
DLNLP mini Project/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI app + /generate endpoint
│   │   ├── model.py      # FLAN-T5-Small loader + generate_text()
│   │   ├── prompts.py    # 4 task-specific prompt templates
│   │   ├── schemas.py    # Pydantic validation models
│   │   └── services.py   # Business logic layer
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── NotesInput.jsx
│   │   │   ├── OutputSelector.jsx
│   │   │   ├── ResultCard.jsx
│   │   │   └── Loading.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
└── README.md
```

---

## 7. Deep Learning Component

> **Important:** This application uses a **pretrained FLAN-T5-Small Transformer model** and performs **local inference**. **No model training or fine-tuning is performed.**

### What is Deep Learning?

Deep Learning is a subfield of Machine Learning where artificial neural networks with many layers learn to extract complex patterns from data. The model used in this project (FLAN-T5-Small) was trained by Google on hundreds of billions of text tokens using Deep Learning techniques.

### What is a Transformer?

A Transformer is a neural network architecture introduced in the paper "Attention Is All You Need" (Vaswani et al., 2017). It uses a mechanism called **self-attention** to understand relationships between words in a sentence, regardless of their position. FLAN-T5 uses an **encoder-decoder Transformer** architecture:

- **Encoder**: Reads and understands the input text (study notes + instruction)
- **Decoder**: Generates the output text token by token

### What is inference?

When we run the model to generate output for new input, this is called **inference**. We are using the model's pre-learned weights (billions of learned parameters) without modifying them.

### Key PyTorch concepts used:

```python
model.eval()          # Inference mode — disables Dropout
torch.no_grad()       # No gradient computation — saves memory
model.generate(...)   # Autoregressive text generation
```

---

## 8. NLP Component

### Natural Language Processing Tasks

| Task | NLP Category | Description |
|---|---|---|
| Summary | Abstractive Summarization | Generates new text that captures the essence |
| Key Points | Extractive-like Information Extraction | Identifies and reformulates key concepts |
| Quiz | Question Generation | Creates Q&A pairs from content |
| Flashcards | Structured Knowledge Extraction | Creates front/back memory cards |

### What is Tokenization?

The model cannot process raw text. The **tokenizer** converts text into **token IDs** (integers) that the model understands:

```
"Photosynthesis uses sunlight" 
  → Tokenizer → [5765, 31, 18, 1, 456, 3] 
  → Model 
  → [17, 3, 8, 42, ...] 
  → Tokenizer → "Plants use sunlight to produce glucose"
```

---

## 9. About FLAN-T5

**FLAN** = Fine-tuned LAnguage Net  
**T5** = Text-To-Text Transfer Transformer  
**Small** = Smallest variant (~80M parameters)

FLAN-T5 was developed by Google and trained on **1800+ NLP tasks** using natural language instructions. This means it can follow instructions like _"Summarize the following notes..."_ without any additional training.

The T5 architecture treats every NLP task as a text-to-text problem:
- Input: A text instruction + content
- Output: Text result

---

## 10. Why FLAN-T5-Small Was Selected

| Criterion | FLAN-T5-Small | Reason |
|---|---|---|
| RAM usage | ~1.2–1.5 GB | Fits in 8 GB RAM laptop |
| Parameters | ~80M | Small enough for CPU inference |
| CPU inference | ✅ Yes | No GPU required |
| Quality | Good for short NLP tasks | Instruction-tuned on 1800+ tasks |
| License | Apache 2.0 | Free for educational use |
| Download size | ~300 MB | Manageable on normal internet |

Larger models (FLAN-T5-base, FLAN-T5-large, BART-large) would require significantly more RAM and would be too slow for CPU inference on a standard laptop.

---

## 11. CPU Inference Settings

```python
MAX_INPUT_TOKENS = 512    # Prevents memory overflow
MAX_NEW_TOKENS   = 200    # Limits output length (~150 words)
NUM_BEAMS        = 2      # Slight quality improvement over greedy
DO_SAMPLE        = False  # Deterministic, faster output
EARLY_STOPPING   = True   # Stop when output is complete
```

Expected inference time on a medium CPU: **20–60 seconds**

---

## 12. Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm 9 or higher

### Step 1: Clone / Download the project

```
DLNLP mini Project/
├── backend/
└── frontend/
```

### Step 2: Set up the Python backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install CPU-only PyTorch first (saves ~2 GB vs CUDA build)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

### Step 3: Set up the React frontend

```bash
cd frontend
npm install
```

---

## 13. Running the Backend

```bash
cd backend

# Activate virtual environment first!
venv\Scripts\activate

# Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**On first run**, the model will be downloaded from Hugging Face (~300 MB). Subsequent runs use the cached model.

You should see:
```
Loading FLAN-T5-Small... (this may take 30-60 seconds on first run)
Model ready. Server is accepting requests.
INFO: Uvicorn running on http://127.0.0.1:8000
```

API documentation is available at: http://localhost:8000/docs

---

## 14. Running the Frontend

Open a **new terminal** (keep the backend running):

```bash
cd frontend
npm run dev
```

Open your browser at: **http://localhost:5173**

---

## 15. Example Input

```
Photosynthesis is the process by which plants use sunlight, water, and CO2 
to produce glucose (C6H12O6) and oxygen. It occurs in two stages:

1. Light-dependent reactions (thylakoid membrane):
   - Chlorophyll absorbs sunlight
   - Water is split (photolysis), releasing O2
   - ATP and NADPH are produced

2. Calvin Cycle (stroma):
   - CO2 is fixed using ATP and NADPH
   - Glucose is synthesized using RuBisCO enzyme

Factors affecting photosynthesis rate: light intensity, CO2 concentration, 
temperature, and water availability.
```

---

## 16. Example Output

**Summary:**
```
Photosynthesis is a process in which plants use sunlight, water, and carbon dioxide 
to make glucose and oxygen. It occurs in two stages: the light-dependent stage in 
the thylakoid membrane and the Calvin cycle in the stroma.
```

**Key Points:**
```
- Photosynthesis converts sunlight, water, and CO2 into glucose and oxygen
- It occurs in two stages: light-dependent reactions and the Calvin cycle
- Chlorophyll absorbs sunlight in the thylakoid membrane
- RuBisCO is the key enzyme in the Calvin cycle
- Light intensity, CO2, temperature, and water affect the photosynthesis rate
```

---

## 17. Hardware Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 6 GB | 8 GB |
| CPU | Dual-core 2 GHz | Quad-core 2.5+ GHz |
| GPU | Not required | Not required |
| Disk space | 1 GB (model cache) | 2 GB |
| Internet | Required (first run only) | — |

---

## 18. Limitations

1. **Inference speed**: CPU inference takes 20–60 seconds per request. A GPU would reduce this to under 2 seconds, but is not required.
2. **Input length**: Limited to 6000 characters (~512 tokens). Longer documents should be split into sections.
3. **Output quality**: FLAN-T5-Small is a small model. Output quality is good for short educational content but may be imperfect for complex technical topics.
4. **Language**: English only in the current version.
5. **No persistence**: Generated content is not saved between sessions.
6. **Single task at a time**: Generating multiple output types simultaneously is not supported (by design, to reduce CPU load).

---

## 19. Future Improvements

The following enhancements are planned for future versions but are **not implemented** in this version:

| Enhancement | Description |
|---|---|
| Larger models | FLAN-T5-Base or FLAN-T5-Large for better quality (requires more RAM) |
| GPU acceleration | CUDA support for sub-second inference |
| Fine-tuning | Train on educational datasets for domain-specific improvement |
| PDF / DOCX upload | Allow students to upload documents directly |
| OCR | Extract text from scanned notes or images |
| Multiple languages | Support for non-English study notes |
| User accounts | Save and manage multiple note sets |
| Cloud deployment | Deploy to AWS/GCP for shared access |
| Batch processing | Generate all 4 outputs simultaneously (with a GPU) |

---

## API Reference

### `GET /health`
Returns server and model status.

```json
{
  "status": "ok",
  "model_loaded": true
}
```

### `POST /generate`
Generates study material from notes.

**Request:**
```json
{
  "text": "Your study notes here...",
  "task": "summary"
}
```

**task options:** `summary` | `key_points` | `quiz` | `flashcards`

**Response:**
```json
{
  "result": "Generated content..."
}
```

---

## Acknowledgements

- **Google Research** — FLAN-T5 model
- **Hugging Face** — Transformers library
- **Meta AI** — PyTorch framework
- Original T5 paper: "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer" (Raffel et al., 2019)
- FLAN paper: "Finetuned Language Models Are Zero-Shot Learners" (Wei et al., 2021)
