/**
 * NotesInput.jsx
 * --------------
 * Large textarea for pasting study notes with live word & character counters.
 *
 * Props:
 *   value       {string}   - Current textarea value
 *   onChange    {function} - Change handler
 *   disabled    {boolean}  - Disable input during generation
 */

const MAX_CHARS = 20000;

export default function NotesInput({ value, onChange, disabled }) {
  const charCount = value.length;
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;
  const isNearLimit = charCount > MAX_CHARS * 0.85;
  const isOverLimit = charCount > MAX_CHARS;

  return (
    <div className="glass-card p-5 transition-all duration-200 focus-within:border-indigo-500/40">
      {/* Section label & stats */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.6)]" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Source Study Notes
          </span>
        </div>

        {/* Live Word & Char Counter */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">
            {wordCount.toLocaleString()} {wordCount === 1 ? "word" : "words"}
          </span>
          <span className="text-slate-600">·</span>
          <span
            className={`font-semibold transition-colors duration-200 ${
              isOverLimit
                ? "text-rose-400"
                : isNearLimit
                ? "text-amber-400"
                : "text-slate-400"
            }`}
          >
            {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} chars
          </span>
        </div>
      </div>

      {/* Textarea */}
      <textarea
        id="notes-input"
        className="notes-textarea"
        placeholder="Paste your study notes, textbook excerpt, or lecture transcript here…&#10;&#10;Examples:&#10;• Biology: Photosynthesis stages, light reactions, Calvin cycle…&#10;• Computer Science: Binary search trees, time complexity, sorting algorithms…&#10;• History / Literature: Causes of World War I, key figures, treaty terms…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={9}
        aria-label="Study notes input"
        style={{ opacity: disabled ? 0.6 : 1 }}
      />

      {/* Footer hint */}
      <div className="border-t border-white/5 mt-3 pt-3 flex items-center justify-between">
        <p className="text-xs text-slate-500 flex items-center gap-1.5">
          <span>💡</span>
          <span>Tip: The model works on any subject — biology, physics, computer science, or history.</span>
        </p>
      </div>

      {/* Over-limit alert */}
      {isOverLimit && (
        <p className="mt-2 text-xs text-rose-400 flex items-center gap-1.5 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
          <span>⚠</span>
          <span>Input exceeds the {MAX_CHARS.toLocaleString()} character limit. Please shorten your notes.</span>
        </p>
      )}
    </div>
  );
}
