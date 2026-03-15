"use client";

const PLATFORMS = [
  { id: "claude_code", label: "Claude Code", color: "#f97316" },
  { id: "cursor",      label: "Cursor",      color: "#6366f1" },
  { id: "copilot",     label: "Copilot",     color: "#22c55e" },
  { id: "continue",    label: "Continue",    color: "#06b6d4" },
  { id: "universal",   label: "Universal",   color: "#a855f7" },
];

interface Props {
  selected: string;
  onChange: (platform: string) => void;
}

export default function PlatformSelector({ selected, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {PLATFORMS.map((p) => {
        const active = selected === p.id;
        return (
          <button
            key={p.id}
            onClick={() => onChange(p.id)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
            style={{
              background: active ? `${p.color}14` : "rgba(255,255,255,0.04)",
              border: `1px solid ${active ? `${p.color}35` : "rgba(255,255,255,0.08)"}`,
              color: active ? p.color : "rgba(255,255,255,0.38)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ background: active ? p.color : "rgba(255,255,255,0.2)" }}
            />
            {p.label}
          </button>
        );
      })}
    </div>
  );
}
