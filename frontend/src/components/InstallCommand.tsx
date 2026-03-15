"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";

const PLATFORM_LABELS: Record<string, string> = {
  claude_code: "Claude Code",
  cursor:      "Cursor",
  copilot:     "GitHub Copilot",
  continue:    "Continue.dev",
  universal:   "Universal",
};

interface Props {
  command: string;
  platform: string;
}

export default function InstallCommand({ command, platform }: Props) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl overflow-hidden border border-white/10">
      {/* Terminal chrome */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-white/[0.04] border-b border-white/8">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-white/10" />
          <div className="w-3 h-3 rounded-full bg-white/10" />
          <div className="w-3 h-3 rounded-full bg-white/10" />
        </div>
        <span className="flex-1 text-center font-mono text-xs text-white/25">
          {PLATFORM_LABELS[platform] ?? platform}
        </span>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check size={12} className="text-green-400" />
              <span className="text-green-400 font-mono">copied</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span className="font-mono">copy</span>
            </>
          )}
        </button>
      </div>

      {/* Command body */}
      <div className="bg-black/50 px-5 py-4 flex items-start gap-3 overflow-x-auto">
        <span className="text-green-400/50 font-mono text-sm shrink-0 mt-px select-none">$</span>
        <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap break-all leading-relaxed">
          {command}
        </pre>
      </div>
    </div>
  );
}
