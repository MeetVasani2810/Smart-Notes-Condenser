/**
 * Header.jsx
 * ----------
 * Application header with title, subtitle, and live hybrid engine status badge.
 */

export default function Header() {
  return (
    <header className="text-center pt-10 pb-6 px-4">
      {/* Engine Status Badge */}
      <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full mb-4
                      border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium shadow-sm backdrop-blur-md">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span>Hybrid Engine: <strong className="text-white font-semibold">Groq LPU</strong> + Local <strong className="text-white font-semibold">FLAN-T5</strong> Fallback</span>
      </div>

      {/* Main Title */}
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
        <span className="text-white drop-shadow-sm">Smart Notes</span>{" "}
        <span
          className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400"
        >
          Condenser
        </span>
      </h1>

      {/* Subtitle */}
      <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
        Transform student study notes into concise summaries, key points, self-test quizzes, and flashcards using{" "}
        <span className="text-indigo-300 font-medium">Deep Learning</span> &{" "}
        <span className="text-indigo-300 font-medium">NLP</span>.
      </p>
    </header>
  );
}
