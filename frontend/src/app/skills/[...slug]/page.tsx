"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowSquareOut, Star, DownloadSimple, Lightning, Tag, Terminal, BookOpen, CaretDown, CaretUp } from "@phosphor-icons/react";
import Link from "next/link";
import { api, type Skill } from "@/lib/api";

const PLATFORM_LABELS: Record<string, string> = {
  claude_code: "Claude Code",
  cursor:      "Cursor",
  copilot:     "GitHub Copilot",
  continue:    "Continue.dev",
  universal:   "Universal",
};

const CAT_STYLES: Record<string, { text: string; bg: string; border: string }> = {
  frontend:       { text: "#60a5fa", bg: "rgba(96,165,250,0.08)",  border: "rgba(96,165,250,0.2)"  },
  backend:        { text: "#4ade80", bg: "rgba(74,222,128,0.08)",  border: "rgba(74,222,128,0.2)"  },
  fullstack:      { text: "#c084fc", bg: "rgba(192,132,252,0.08)", border: "rgba(192,132,252,0.2)" },
  devops:         { text: "#fb923c", bg: "rgba(251,146,60,0.08)",  border: "rgba(251,146,60,0.2)"  },
  "ml-ai":        { text: "#f472b6", bg: "rgba(244,114,182,0.08)", border: "rgba(244,114,182,0.2)" },
  security:       { text: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.2)" },
  database:       { text: "#22d3ee", bg: "rgba(34,211,238,0.08)",  border: "rgba(34,211,238,0.2)"  },
  testing:        { text: "#facc15", bg: "rgba(250,204,21,0.08)",  border: "rgba(250,204,21,0.2)"  },
  cloud:          { text: "#38bdf8", bg: "rgba(56,189,248,0.08)",  border: "rgba(56,189,248,0.2)"  },
  mobile:         { text: "#818cf8", bg: "rgba(129,140,248,0.08)", border: "rgba(129,140,248,0.2)" },
  "data-science": { text: "#a3e635", bg: "rgba(163,230,53,0.08)",  border: "rgba(163,230,53,0.2)"  },
};
const DEFAULT_CAT = { text: "rgba(255,255,255,0.4)", bg: "rgba(255,255,255,0.05)", border: "rgba(255,255,255,0.1)" };

export default function SkillDetailPage() {
  const params    = useParams();
  const slug      = (params.slug as string[]).join("/");

  const [skill, setSkill]           = useState<Skill | null>(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState("");
  const [showContent, setShowContent] = useState(false);
  const [copied, setCopied]         = useState(false);

  useEffect(() => {
    api.skills.get(slug)
      .then(setSkill)
      .catch(() => setError("Skill not found"))
      .finally(() => setLoading(false));
  }, [slug]);

  const copyCommand = () => {
    if (!skill?.install_command) return;
    navigator.clipboard.writeText(skill.install_command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <Spinner />;
  if (error || !skill) return <NotFound slug={slug} />;

  const cat = CAT_STYLES[skill.primary_category] ?? DEFAULT_CAT;
  const qualityPct = Math.min((skill.quality_score / 10) * 100, 100);

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{ background: `radial-gradient(ellipse 60% 35% at 50% -8%, ${cat.text}10 0%, transparent 55%)` }}
      />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-700 flex items-center justify-center">
              <Lightning size={14} className="text-white" />
            </div>
            <span className="font-bold tracking-tight">SkillPack</span>
          </Link>
          <Link href="/explore" className="flex items-center gap-1.5 text-sm text-white/35 hover:text-white transition-colors">
            <ArrowLeft size={13} /> Browse skills
          </Link>
        </div>
      </nav>

      <div className="relative max-w-4xl mx-auto px-6 py-12">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-10"
        >
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span
              className="text-xs font-medium border rounded-md px-2.5 py-1"
              style={{ color: cat.text, background: cat.bg, borderColor: cat.border }}
            >
              {skill.primary_category}
            </span>
            {skill.platforms.slice(0, 3).map((p) => (
              <span key={p} className="text-xs text-white/28 border border-white/10 rounded-md px-2.5 py-1">
                {PLATFORM_LABELS[p] ?? p}
              </span>
            ))}
          </div>

          <h1 className="text-4xl font-bold mb-3 leading-tight">{skill.name}</h1>
          <p className="text-white/45 text-base leading-relaxed max-w-2xl">
            {skill.description || "No description available."}
          </p>

          {/* Stats row */}
          <div className="flex flex-wrap items-center gap-5 mt-6">
            {/* Quality bar */}
            <div className="flex items-center gap-2.5">
              <Star size={13} className="text-yellow-400/70" />
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${qualityPct}%` }}
                    transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: cat.text }}
                  />
                </div>
                <span className="font-mono text-xs text-white/40">{skill.quality_score.toFixed(1)}</span>
              </div>
            </div>

            <span className="flex items-center gap-1.5 font-mono text-xs text-white/30">
              <DownloadSimple size={12} />
              {(skill.install_count || 0).toLocaleString()} installs
            </span>

            {skill.github_stars > 0 && (
              <span className="flex items-center gap-1.5 font-mono text-xs text-white/30">
                <Star size={12} />
                {skill.github_stars.toLocaleString()} stars
              </span>
            )}

            <span className="font-mono text-[11px] text-white/18 ml-auto hidden sm:block">{skill.slug}</span>
          </div>
        </motion.div>

        {/* Install command */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden mb-8"
        >
          <div className="flex items-center gap-2 px-5 py-3.5 border-b border-white/[0.06]">
            <Terminal size={13} style={{ color: cat.text }} />
            <h2 className="text-xs font-semibold text-white/55 uppercase tracking-widest">Install</h2>
          </div>

          {/* Terminal body */}
          <div className="flex items-center gap-3 px-5 py-4 bg-black/40">
            <span className="font-mono text-green-400/50 text-sm select-none">$</span>
            <code className="flex-1 font-mono text-sm text-green-400 break-all">{skill.install_command}</code>
            <button
              onClick={copyCommand}
              className="shrink-0 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: copied ? "rgba(34,197,94,0.14)" : `${cat.text}14`,
                border: `1px solid ${copied ? "rgba(34,197,94,0.3)" : `${cat.text}28`}`,
                color: copied ? "#4ade80" : cat.text,
              }}
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>

          {skill.source_url && (
            <div className="px-5 py-2.5 border-t border-white/[0.05]">
              <a
                href={skill.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-white/25 hover:text-white/50 transition-colors"
              >
                <ArrowSquareOut size={11} /> View on GitHub
              </a>
            </div>
          )}
        </motion.div>

        {/* Tags + keywords */}
        {(skill.tags?.length > 0 || skill.sub_categories?.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.16 }}
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 mb-8"
          >
            <div className="flex items-center gap-2 mb-4">
              <Tag size={13} className="text-white/35" />
              <h2 className="text-xs font-semibold text-white/55 uppercase tracking-widest">Tags</h2>
            </div>

            <div className="flex flex-wrap gap-2">
              {skill.sub_categories?.map((sc) => (
                <span
                  key={sc}
                  className="text-xs font-medium rounded-lg px-2.5 py-1"
                  style={{ color: cat.text, background: `${cat.text}12`, border: `1px solid ${cat.text}22` }}
                >
                  {sc}
                </span>
              ))}
              {skill.tags?.map((tag) => (
                <span key={tag} className="text-xs text-white/38 bg-white/[0.05] border border-white/10 rounded-lg px-2.5 py-1">
                  {tag}
                </span>
              ))}
            </div>

            {(skill.role_keywords?.length > 0 || skill.task_keywords?.length > 0) && (
              <div className="mt-5 pt-5 border-t border-white/[0.06] grid grid-cols-2 gap-6 text-xs">
                {skill.role_keywords?.length > 0 && (
                  <div>
                    <p className="text-white/22 mb-2 uppercase tracking-widest text-[10px]">Roles</p>
                    <div className="flex flex-wrap gap-1.5">
                      {skill.role_keywords.map((r) => (
                        <span key={r} className="text-white/38 bg-white/[0.04] border border-white/8 rounded-md px-2 py-0.5">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {skill.task_keywords?.length > 0 && (
                  <div>
                    <p className="text-white/22 mb-2 uppercase tracking-widest text-[10px]">Tasks</p>
                    <div className="flex flex-wrap gap-1.5">
                      {skill.task_keywords.map((t) => (
                        <span key={t} className="text-white/38 bg-white/[0.04] border border-white/8 rounded-md px-2 py-0.5">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Raw SKILL.md */}
        {skill.raw_content && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.22 }}
            className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden mb-8"
          >
            <button
              onClick={() => setShowContent((v) => !v)}
              className="w-full flex items-center justify-between px-6 py-4 hover:bg-white/[0.03] transition-colors"
            >
              <div className="flex items-center gap-2">
                <BookOpen size={13} className="text-white/35" />
                <span className="text-xs font-semibold text-white/55 uppercase tracking-widest">SKILL.md Content</span>
              </div>
              {showContent ? (
                <CaretUp size={13} className="text-white/25" />
              ) : (
                <CaretDown size={13} className="text-white/25" />
              )}
            </button>

            <AnimatePresence>
              {showContent && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-6 border-t border-white/[0.06]">
                    <pre className="mt-4 text-xs text-white/50 font-mono whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                      {skill.raw_content}
                    </pre>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        <div className="text-center pt-2">
          <Link href="/explore" className="text-sm text-white/25 hover:text-white transition-colors font-mono">
            ← Browse all skills
          </Link>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div className="min-h-screen bg-[#060606] text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-white/15 border-t-violet-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white/35 text-sm font-mono">Loading skill…</p>
      </div>
    </div>
  );
}

function NotFound({ slug }: { slug: string }) {
  return (
    <div className="min-h-screen bg-[#060606] text-white flex items-center justify-center">
      <div className="text-center">
        <p className="text-white/40 mb-2 text-lg">Skill not found</p>
        <p className="font-mono text-white/22 text-sm mb-6">{slug}</p>
        <Link href="/explore" className="text-sm text-violet-400 hover:underline">← Browse all skills</Link>
      </div>
    </div>
  );
}
