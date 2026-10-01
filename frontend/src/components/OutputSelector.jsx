/**
 * OutputSelector.jsx
 * ------------------
 * 4 Study output formats: Summary, Key Points, Quiz (Self-Test), Flashcards (Flip).
 *
 * Props:
 *   selected   {string}   - Currently selected task ID
 *   onChange   {function} - Task change callback
 *   disabled   {boolean}  - Disable buttons during generation
 */

const TASKS = [
  {
    id: "summary",
    label: "Summary",
    icon: "📄",
    description: "Abstractive Overview",
  },
  {
    id: "key_points",
    label: "Key Points",
    icon: "🔑",
    description: "5 Core Bullets",
  },
  {
    id: "quiz",
    label: "Quiz",
    icon: "❓",
    description: "Self-Test & Answers",
  },
  {
    id: "flashcards",
    label: "Flashcards",
    icon: "🃏",
    description: "5 Interactive Cards",
  },
];

export default function OutputSelector({ selected, onChange, disabled }) {
  return (
    <div className="glass-card p-5">
      {/* Section label */}
      <div className="flex items-center gap-2 mb-3.5">
        <div className="w-2.5 h-2.5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.6)]" />
        <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Target Study Material
        </span>
      </div>

      {/* Task buttons grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {TASKS.map((task) => {
          const isActive = selected === task.id;
          return (
            <button
              key={task.id}
              id={`task-${task.id}`}
              onClick={() => !disabled && onChange(task.id)}
              disabled={disabled}
              aria-pressed={isActive}
              className={`task-btn group ${isActive ? "task-btn-active" : ""} ${
                disabled ? "cursor-not-allowed opacity-50" : ""
              }`}
            >
              <span className="text-2xl transition-transform duration-200 group-hover:scale-110">
                {task.icon}
              </span>
              <span className="font-semibold text-sm text-slate-100">{task.label}</span>
              <span className="text-[11px] opacity-75 font-normal">{task.description}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
