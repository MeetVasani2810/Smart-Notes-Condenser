/**
 * ResultCard.jsx
 * --------------
 * Displays the AI-generated study material with task-specific rendering:
 *   - Summary:    Clean paragraph format with academic left-border accent
 *   - Key Points: Structured numbered cards (1–5)
 *   - Quiz:       Interactive Self-Test mode with "Check Answer" reveal buttons
 *   - Flashcards: Interactive flip cards with Front/Back active recall
 *
 * Props:
 *   result    {string} - Generated text from the backend
 *   task      {string} - "summary" | "key_points" | "quiz" | "flashcards"
 *   modelUsed {string} - Active inference model engine name
 */

import { useState } from "react";

const TASK_META = {
  summary:    { label: "Abstractive Summary", icon: "📄", desc: "Overview of key concepts" },
  key_points: { label: "Key Points",         icon: "🔑", desc: "5 essential takeaways" },
  quiz:       { label: "Self-Test Quiz",      icon: "❓", desc: "Active recall test" },
  flashcards: { label: "Study Flashcards",   icon: "🃏", desc: "5 memory flip cards" },
};

// ─────────────────────────────────────────────────────────────────────────────
// Parsers
// ─────────────────────────────────────────────────────────────────────────────

function parseKeyPoints(text) {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);

  const listLines = lines.filter((l) => /^(\d+[\.\)]|[-•])\s/.test(l));
  if (listLines.length >= 2) {
    return listLines
      .map((line) => line.replace(/^\d+[\.\)]\s*/, "").replace(/^[-•]\s*/, "").trim())
      .filter(Boolean);
  }

  if (lines.length >= 3) {
    return lines
      .map((l) => l.replace(/^\d+[\.\)]\s*/, "").replace(/^[-•]\s*/, "").trim())
      .filter(Boolean);
  }

  const joined = lines.join(" ");
  const parts = joined
    .split(/(?:[\.!?])\s+(?=[A-Z2-9])|(?:\s+)(?=[2-9]\.\s)/)
    .map((s) => s.replace(/^\d+[\.\)]\s*/, "").trim())
    .filter((s) => s.length > 8);

  return parts.length >= 2 ? parts : lines.filter(Boolean);
}

function parseQuiz(text) {
  const pairs = [];
  const blocks = text.split(/\n\s*\n/).filter((b) => b.trim());

  for (const block of blocks) {
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    let question = "";
    let answer = "";

    for (const line of lines) {
      if (/^(Q\d*[:.]|Question\s*\d*[:.])/i.test(line)) {
        question = line.replace(/^(Q\d*[:.]|Question\s*\d*[:.]\s*)/i, "").trim();
      } else if (/^(A\d*[:.]|Answer\s*\d*[:.])/i.test(line)) {
        answer = line.replace(/^(A\d*[:.]|Answer\s*\d*[:.]\s*)/i, "").trim();
      }
    }

    if (question) {
      pairs.push({ question, answer });
    }
  }

  if (pairs.length === 0) {
    const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
    let currentQ = null;
    for (const line of lines) {
      if (/^(Q\d*[:.]|Question\s*\d*[:.])/i.test(line)) {
        currentQ = line.replace(/^(Q\d*[:.]|Question\s*\d*[:.]\s*)/i, "").trim();
      } else if (/^(A\d*[:.]|Answer\s*\d*[:.])/i.test(line) && currentQ !== null) {
        const ans = line.replace(/^(A\d*[:.]|Answer\s*\d*[:.]\s*)/i, "").trim();
        pairs.push({ question: currentQ, answer: ans });
        currentQ = null;
      }
    }
  }

  return pairs;
}

function parseFlashcards(text) {
  const cards = [];
  const blocks = text.split(/\n\s*\n/).filter((b) => b.trim());

  for (const block of blocks) {
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    let front = "";
    let back = "";

    for (const line of lines) {
      if (/^(Front|Term)\s*[:]/i.test(line)) {
        front = line.replace(/^(Front|Term)\s*[:.]\s*/i, "").trim();
      } else if (/^(Back|Definition)\s*[:]/i.test(line)) {
        back = line.replace(/^(Back|Definition)\s*[:.]\s*/i, "").trim();
      }
    }

    if (front || back) {
      cards.push({ front: front || "—", back: back || "—" });
    }
  }

  return cards;
}

// ─────────────────────────────────────────────────────────────────────────────
// Renderers
// ─────────────────────────────────────────────────────────────────────────────

function SummaryRenderer({ text }) {
  const paragraphs = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return (
    <div className="space-y-4">
      {paragraphs.map((para, i) => (
        <div
          key={i}
          className="p-4 rounded-xl border border-indigo-500/15 bg-surface-900/40 border-l-4 border-l-indigo-400"
        >
          <p className="text-slate-100 text-sm sm:text-base leading-relaxed font-normal">
            {para}
          </p>
        </div>
      ))}
    </div>
  );
}

function KeyPointsRenderer({ text }) {
  const points = parseKeyPoints(text);

  if (points.length === 0) {
    return <p className="text-slate-400 text-sm italic">No key points found.</p>;
  }

  return (
    <div className="space-y-3">
      {points.map((point, i) => (
        <div
          key={i}
          className="p-3.5 rounded-xl border border-indigo-500/15 bg-surface-900/40 flex items-start gap-3.5 hover:border-indigo-500/30 transition-colors"
        >
          <span
            className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
            style={{
              background: "rgba(129,140,248,0.2)",
              color: "#c7d2fe",
              border: "1px solid rgba(129,140,248,0.35)",
            }}
          >
            {i + 1}
          </span>
          <span className="text-slate-200 text-sm sm:text-[15px] leading-relaxed pt-0.5">
            {point}
          </span>
        </div>
      ))}
    </div>
  );
}

function QuizRenderer({ text }) {
  const [revealed, setRevealed] = useState({});
  const pairs = parseQuiz(text);

  if (pairs.length === 0) {
    return <p className="text-slate-400 text-sm italic">Could not parse quiz output.</p>;
  }

  const toggleReveal = (i) => {
    setRevealed((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  const allRevealed = pairs.length > 0 && pairs.every((_, i) => !!revealed[i]);

  const toggleAll = () => {
    if (allRevealed) {
      setRevealed({});
    } else {
      const all = {};
      pairs.forEach((_, i) => {
        all[i] = true;
      });
      setRevealed(all);
    }
  };

  return (
    <div className="space-y-4">
      {/* Quiz Toolbar */}
      <div className="flex items-center justify-between px-1 text-xs text-slate-400 border-b border-white/5 pb-2.5">
        <span className="flex items-center gap-1.5 font-medium">
          <span>🧠</span>
          <span>Self-Test Mode: Think first, then check answer</span>
        </span>
        <button
          onClick={toggleAll}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors underline underline-offset-2"
        >
          {allRevealed ? "Hide All Answers" : "Reveal All Answers"}
        </button>
      </div>

      {pairs.map((pair, i) => {
        const isShown = !!revealed[i];
        return (
          <div
            key={i}
            className="rounded-xl overflow-hidden transition-all duration-200"
            style={{
              border: `1px solid ${isShown ? "rgba(52,211,153,0.35)" : "rgba(129,140,248,0.2)"}`,
              background: "rgba(18, 22, 38, 0.7)",
            }}
          >
            {/* Question row */}
            <div
              className="p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-start justify-between gap-3"
              style={{ background: "rgba(129,140,248,0.08)" }}
            >
              <div className="flex items-start gap-3 flex-1">
                <span
                  className="flex-shrink-0 text-xs font-bold px-2 py-0.5 rounded-md mt-0.5"
                  style={{
                    background: "rgba(129,140,248,0.25)",
                    color: "#a5b4fc",
                    border: "1px solid rgba(129,140,248,0.35)",
                  }}
                >
                  Q{i + 1}
                </span>
                <span className="text-slate-100 text-sm sm:text-[15px] font-semibold leading-relaxed">
                  {pair.question}
                </span>
              </div>

              {/* Check Answer Button */}
              <button
                onClick={() => toggleReveal(i)}
                className="self-end sm:self-start flex-shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-1.5 shadow-sm"
                style={{
                  background: isShown
                    ? "rgba(239,68,68,0.15)"
                    : "linear-gradient(135deg, rgba(99,102,241,0.35), rgba(79,70,229,0.35))",
                  color: isShown ? "#fca5a5" : "#e0e7ff",
                  border: `1px solid ${isShown ? "rgba(239,68,68,0.3)" : "rgba(129,140,248,0.4)"}`,
                }}
              >
                <span>{isShown ? "🙈" : "🔍"}</span>
                <span>{isShown ? "Hide Answer" : "Check Answer"}</span>
              </button>
            </div>

            {/* Answer row */}
            {isShown && (
              <div
                className="p-3.5 sm:p-4 flex items-start gap-3 animate-fade-in border-t"
                style={{
                  background: "rgba(10, 15, 28, 0.8)",
                  borderColor: "rgba(52,211,153,0.25)",
                }}
              >
                <span
                  className="flex-shrink-0 text-xs font-bold px-2 py-0.5 rounded-md mt-0.5"
                  style={{
                    background: "rgba(52,211,153,0.2)",
                    color: "#6ee7b7",
                    border: "1px solid rgba(52,211,153,0.35)",
                  }}
                >
                  A{i + 1}
                </span>
                <span className="text-emerald-100/95 text-sm sm:text-[15px] leading-relaxed">
                  {pair.answer || <em className="text-slate-500">See notes</em>}
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function FlashcardsRenderer({ text }) {
  const [flipped, setFlipped] = useState({});
  const cards = parseFlashcards(text);

  if (cards.length === 0) {
    return <p className="text-slate-400 text-sm italic">Could not parse flashcards.</p>;
  }

  const toggleFlip = (i) =>
    setFlipped((prev) => ({ ...prev, [i]: !prev[i] }));

  return (
    <div className="space-y-3.5">
      <div className="flex items-center justify-between text-xs text-slate-400 px-1 border-b border-white/5 pb-2">
        <span>🃏 Click any card to flip between Front and Back</span>
        <span className="font-mono text-indigo-300">{cards.length} cards</span>
      </div>

      {cards.map((card, i) => {
        const isFlipped = !!flipped[i];
        return (
          <button
            key={i}
            onClick={() => toggleFlip(i)}
            className="w-full text-left rounded-xl overflow-hidden transition-all duration-200 focus:outline-none hover:shadow-lg group"
            style={{
              border: `1px solid ${isFlipped ? "rgba(52,211,153,0.35)" : "rgba(129,140,248,0.25)"}`,
            }}
            aria-label={`Flashcard ${i + 1}: ${isFlipped ? "Back" : "Front"}`}
          >
            {/* Top Label Bar */}
            <div
              className="px-4 py-2 flex items-center justify-between transition-colors"
              style={{
                background: isFlipped
                  ? "rgba(52,211,153,0.12)"
                  : "rgba(129,140,248,0.12)",
              }}
            >
              <div className="flex items-center gap-2">
                <span
                  className="text-xs font-bold px-2 py-0.5 rounded"
                  style={{
                    background: isFlipped ? "rgba(52,211,153,0.2)" : "rgba(129,140,248,0.2)",
                    color: isFlipped ? "#6ee7b7" : "#a5b4fc",
                  }}
                >
                  Card {i + 1}
                </span>
                <span className="text-xs font-semibold text-slate-300">
                  {isFlipped ? "Answer / Back ↩" : "Question / Front"}
                </span>
              </div>
              <span className="text-[11px] text-slate-400 group-hover:text-slate-200 transition-colors">
                {isFlipped ? "click to flip back" : "click to reveal answer 🔄"}
              </span>
            </div>

            {/* Content Body */}
            <div className="px-4 py-3.5" style={{ background: "rgba(15,20,35,0.75)" }}>
              <span className="text-slate-100 text-sm sm:text-[15px] leading-relaxed font-medium">
                {isFlipped ? card.back : card.front}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ResultCard — Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function ResultCard({ result, task, modelUsed }) {
  const [copied, setCopied] = useState(false);
  const meta = TASK_META[task] || { label: "Result", icon: "✨", desc: "AI Output" };
  const engineName = modelUsed || "Groq (Llama 3.3 70B)";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = result;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderContent = () => {
    switch (task) {
      case "summary":
        return <SummaryRenderer text={result} />;
      case "key_points":
        return <KeyPointsRenderer text={result} />;
      case "quiz":
        return <QuizRenderer text={result} />;
      case "flashcards":
        return <FlashcardsRenderer text={result} />;
      default:
        return <p className="text-slate-200 text-sm leading-relaxed">{result}</p>;
    }
  };

  return (
    <div
      id="result-card"
      className="glass-card p-5 animate-slide-up shadow-xl"
      role="region"
      aria-label={`${meta.label} result`}
    >
      {/* Card Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">{meta.icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-white text-base tracking-tight">{meta.label}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">
                ⚡ {engineName}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">{meta.desc}</p>
          </div>
        </div>

        {/* Copy Button */}
        <button
          id="copy-result-btn"
          onClick={handleCopy}
          className="btn-secondary text-xs py-1.5 px-3.5 flex items-center gap-1.5"
          title="Copy full text to clipboard"
        >
          {copied ? (
            <>
              <span className="text-emerald-400">✓</span>
              <span className="text-emerald-300 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <span>📋</span>
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Result Content */}
      <div className="border-t border-white/5 pt-4">
        {renderContent()}
      </div>

      {/* Card Footer */}
      <div className="mt-5 pt-3 border-t border-white/5 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span>🤖</span>
          <span>Engine: <strong className="text-slate-300">{engineName}</strong></span>
        </div>
        <span className="text-[11px] text-emerald-400/80 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
          Offline Fallback Ready
        </span>
      </div>
    </div>
  );
}
