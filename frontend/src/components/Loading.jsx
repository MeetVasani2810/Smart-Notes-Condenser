/**
 * Loading.jsx
 * -----------
 * High-aesthetic loading indicator shown during AI generation.
 */

export default function Loading() {
  return (
    <div
      id="loading-indicator"
      className="glass-card p-8 flex flex-col items-center gap-4 animate-fade-in text-center"
      role="status"
      aria-live="polite"
    >
      {/* Animated Spinner with Glow */}
      <div className="relative flex items-center justify-center">
        <div className="spinner" />
        <div
          className="absolute inset-0 rounded-full opacity-30 animate-ping"
          style={{ background: "rgba(99, 102, 241, 0.4)" }}
        />
      </div>

      {/* Primary message */}
      <div className="space-y-1">
        <p className="text-white font-bold text-base tracking-tight">
          Generating Study Material…
        </p>
        <p className="text-slate-400 text-xs sm:text-sm max-w-sm leading-relaxed">
          Running inference via <span className="text-indigo-300 font-semibold">Groq LPU AI</span> (with local FLAN-T5 offline fallback).
        </p>
      </div>

      {/* Animated Dots */}
      <div className="flex gap-2 mt-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-indigo-400"
            style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
          />
        ))}
      </div>
    </div>
  );
}
