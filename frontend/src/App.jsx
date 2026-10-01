/**
 * App.jsx
 * -------
 * Root component. Manages application state and orchestrates
 * the generate → display flow with the Hybrid AI engine.
 */

import { useState, useCallback } from "react";
import Header from "./components/Header";
import NotesInput from "./components/NotesInput";
import OutputSelector from "./components/OutputSelector";
import ResultCard from "./components/ResultCard";
import Loading from "./components/Loading";
import { generateContent } from "./services/api";

const MAX_CHARS = 20000;

// Example notes for quick viva demonstrations
const SAMPLES = {
  biology: `Photosynthesis is the process by which plants, algae, and some bacteria convert light energy (usually from the sun) into chemical energy stored in glucose (C6H12O6).

The overall chemical equation is:
6CO2 + 6H2O + light energy → C6H12O6 + 6O2

Photosynthesis occurs in two main stages:
1. Light-dependent reactions (in the thylakoid membrane):
   - Chlorophyll absorbs sunlight photons
   - Water molecules are split (photolysis), releasing O2 as a byproduct
   - ATP and NADPH are synthesized as chemical energy carriers

2. Calvin Cycle / Light-independent reactions (in the stroma):
   - CO2 is fixed by the key enzyme RuBisCO
   - ATP and NADPH are consumed to synthesize high-energy glucose (C6H12O6)

Factors affecting the rate of photosynthesis:
- Light intensity (energy input)
- Carbon dioxide concentration (carbon substrate)
- Temperature (enzyme kinetics and RuBisCO efficiency)
- Water availability (photolysis reactant and stomatal regulation)`,

  cs: `Binary Search is an efficient search algorithm for finding the position of a target value within a sorted array.

How it works:
1. Compare the target value to the middle element of the array.
2. If the target equals the middle element, return its index.
3. If the target is less than the middle element, narrow the search interval to the left half.
4. If the target is greater, narrow the search to the right half.
5. Repeat until the target is found or the interval is empty.

Key Properties:
- Prerequisite: The array MUST be sorted.
- Time Complexity: O(log n) worst and average case, O(1) best case.
- Space Complexity: O(1) iterative, O(log n) recursive call stack.
- Comparison: Much faster than Linear Search (O(n)) on large datasets (e.g. searching 1,000,000 elements takes ≤ 20 comparisons).`
};

export default function App() {
  const [notes, setNotes] = useState("");
  const [selectedTask, setSelectedTask] = useState("summary");
  const [result, setResult] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // ── Validation ────────────────────────────────────────────────────────────
  const getValidationError = useCallback(() => {
    const trimmed = notes.trim();
    if (!trimmed) return "Please paste or type your study notes before generating.";
    if (trimmed.length > MAX_CHARS)
      return `Your notes are too long (${trimmed.length.toLocaleString()} characters). Please reduce to under ${MAX_CHARS.toLocaleString()} characters.`;
    return null;
  }, [notes]);

  // ── Generate handler ─────────────────────────────────────────────────────
  const handleGenerate = useCallback(async () => {
    const validationError = getValidationError();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await generateContent(notes.trim(), selectedTask);
      setResult(data.result);
      setModelUsed(data.model_used || "Groq (Llama 3.3 70B)");
    } catch (err) {
      if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        setError(
          "Request timed out. Please try again with shorter notes."
        );
      } else if (err.response) {
        const detail = err.response.data?.detail || "An error occurred on the server.";
        setError(detail);
      } else if (err.request) {
        setError(
          "Could not connect to the backend server. Make sure the FastAPI backend is running on http://localhost:8000."
        );
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [notes, selectedTask, getValidationError]);

  // ── Clear handler ─────────────────────────────────────────────────────────
  const handleClear = useCallback(() => {
    setNotes("");
    setResult(null);
    setModelUsed(null);
    setError(null);
  }, []);

  // ── Load sample notes ─────────────────────────────────────────────────────
  const handleLoadSample = useCallback((key) => {
    setNotes(SAMPLES[key] || "");
    setResult(null);
    setModelUsed(null);
    setError(null);
  }, []);

  const canGenerate = notes.trim().length > 0 && notes.length <= MAX_CHARS && !isLoading;

  return (
    <div className="min-h-screen">
      <div className="max-w-2xl mx-auto px-4 pb-16">

        {/* ── Header ── */}
        <Header />

        {/* ── Main Content ── */}
        <main className="mt-2 flex flex-col gap-4">

          {/* Notes Input */}
          <NotesInput
            value={notes}
            onChange={setNotes}
            disabled={isLoading}
          />

          {/* Load Sample Notes Links */}
          {notes.length === 0 && (
            <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
              <span className="font-medium">Quick Demo Samples:</span>
              <button
                id="load-sample-bio"
                onClick={() => handleLoadSample("biology")}
                className="px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 hover:bg-indigo-500/20 transition-colors"
              >
                🌿 Photosynthesis (Bio)
              </button>
              <button
                id="load-sample-cs"
                onClick={() => handleLoadSample("cs")}
                className="px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 hover:bg-indigo-500/20 transition-colors"
              >
                💻 Binary Search (CS)
              </button>
            </div>
          )}

          {/* Output Selector */}
          <OutputSelector
            selected={selectedTask}
            onChange={setSelectedTask}
            disabled={isLoading}
          />

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              id="generate-btn"
              onClick={handleGenerate}
              disabled={!canGenerate}
              className="btn-primary flex-1 py-3.5 text-base font-bold shadow-lg"
            >
              {isLoading ? (
                <>
                  <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                  Generating Study Material…
                </>
              ) : (
                <>
                  <span>✨</span>
                  Generate Study Material
                </>
              )}
            </button>

            <button
              id="clear-btn"
              onClick={handleClear}
              disabled={isLoading || notes.length === 0}
              className="btn-secondary px-5"
            >
              <span>✕</span>
              Clear
            </button>
          </div>

          {/* Error Message Alert */}
          {error && (
            <div
              id="error-message"
              className="glass-card p-4 border-rose-500/40 bg-rose-950/30 animate-fade-in"
              role="alert"
            >
              <div className="flex items-start gap-3">
                <span className="text-rose-400 text-lg flex-shrink-0">⚠</span>
                <p className="text-rose-200 text-sm leading-relaxed">{error}</p>
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {isLoading && <Loading />}

          {/* Result Card */}
          {result && !isLoading && (
            <ResultCard result={result} task={selectedTask} modelUsed={modelUsed} />
          )}
        </main>

        {/* ── Footer ── */}
        <footer className="mt-14 text-center text-xs text-slate-500 space-y-1">
          <p>
            Smart Notes Condenser · Deep Learning & NLP Course Project
          </p>
          <p className="text-slate-600 text-[11px]">
            Primary: Groq Cloud LPU · Offline Fallback: Local PyTorch FLAN-T5-Small CPU
          </p>
        </footer>
      </div>
    </div>
  );
}
