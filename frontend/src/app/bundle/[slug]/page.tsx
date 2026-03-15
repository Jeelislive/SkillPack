"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, DownloadSimple, Package, ArrowSquareOut, CaretDown, CaretUp, Lightning, Star } from "@phosphor-icons/react";
import Link from "next/link";
import PlatformSelector from "@/components/PlatformSelector";
import InstallCommand from "@/components/InstallCommand";
import { api, type Bundle, type Skill } from "@/lib/api";

const CAT_COLORS: Record<string, { text: string; bg: string; border: string }> = {
  frontend:  { text: "#60a5fa", bg: "rgba(96,165,250,0.08)",  border: "rgba(96,165,250,0.2)"  },
  backend:   { text: "#4ade80", bg: "rgba(74,222,128,0.08)",  border: "rgba(74,222,128,0.2)"  },
  fullstack: { text: "#c084fc", bg: "rgba(192,132,252,0.08)", border: "rgba(192,132,252,0.2)" },
  devops:    { text: "#fb923c", bg: "rgba(251,146,60,0.08)",  border: "rgba(251,146,60,0.2)"  },
  "ml-ai":   { text: "#f472b6", bg: "rgba(244,114,182,0.08)", border: "rgba(244,114,182,0.2)" },
  security:  { text: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.2)" },
  database:  { text: "#22d3ee", bg: "rgba(34,211,238,0.08)",  border: "rgba(34,211,238,0.2)"  },
  testing:   { text: "#facc15", bg: "rgba(250,204,21,0.08)",  border: "rgba(250,204,21,0.2)"  },
};
const DEFAULT_CAT = { text: "rgba(255,255,255,0.45)", bg: "rgba(255,255,255,0.05)", border: "rgba(255,255,255,0.12)" };

const SKILL_CAT_COLORS: Record<string, string> = {
  frontend: "#60a5fa", backend: "#4ade80", fullstack: "#c084fc",
  devops: "#fb923c", "ml-ai": "#f472b6", security: "#f87171",
  database: "#22d3ee", testing: "#facc15", cloud: "#38bdf8",
};

export default function BundlePage() {
  const params = useParams();
  const slug = params.slug as string;

  const [bundle, setBundle]       = useState<Bundle | null>(null);
  const [platform, setPlatform]   = useState("claude_code");
  const [loading, setLoading]     = useState(true);
  const [expanded, setExpanded]   = useState<Set<number>>(new Set());
  const [error, setError]         = useState("");

  useEffect(() => {
    api.bundles.get(slug)
      .then(setBundle)
      .catch(() => setError("Bundle not found"))
      .finally(() => setLoading(false));
  }, [slug]);

  const toggle = (id: number) =>
    setExpanded((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  if (loading) return <Spinner label="Loading bundle…" />;
  if (error || !bundle) return <NotFound />;

  const cat = CAT_COLORS[bundle.category] ?? DEFAULT_CAT;
  const cmd = bundle.commands?.[platform] ?? "";

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{ background: `radial-gradient(ellipse 70% 40% at 50% -10%, ${cat.text}10 0%, transparent 60%)` }}
      />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-700 flex items-center justify-center">
              <Lightning size={14} className="text-white" />
            </div>
            <span className="font-bold tracking-tight">SkillPack</span>
          </Link>
          <Link href="/explore" className="flex items-center gap-1.5 text-sm text-white/35 hover:text-white transition-colors">
            <ArrowLeft size={13} /> Browse
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
          <div className="flex items-center gap-2 mb-4">
            <span
              className="text-xs font-medium border rounded-md px-2.5 py-1 font-mono"
              style={{ color: cat.text, background: cat.bg, borderColor: cat.border }}
            >
              {bundle.type}
            </span>
            <span className="text-xs text-white/28">{bundle.category}</span>
          </div>

          <h1 className="text-4xl font-bold mb-3">{bundle.name}</h1>
          <p className="text-white/45 text-base leading-relaxed max-w-2xl">{bundle.description}</p>

          <div className="flex items-center gap-5 mt-5 text-xs font-mono text-white/28">
            <span className="flex items-center gap-1.5">
              <Package size={12} /> {bundle.skill_count} skills
            </span>
            <span className="flex items-center gap-1.5">
              <DownloadSimple size={12} /> {bundle.install_count.toLocaleString()} installs
            </span>
          </div>
        </motion.div>

        {/* Install */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 mb-10"
        >
          <h2 className="text-sm font-semibold text-white/60 mb-5 uppercase tracking-widest text-xs">Install Command</h2>
          <div className="mb-5">
            <PlatformSelector selected={platform} onChange={setPlatform} />
          </div>
          {cmd ? (
            <InstallCommand command={cmd} platform={platform} />
          ) : (
            <div className="text-sm text-white/28 py-3 font-mono">
              No command available for this platform yet.
            </div>
          )}
        </motion.div>

        {/* Skills list */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.18 }}
        >
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold">Included Skills</h2>
            <span className="font-mono text-xs text-white/28">{bundle.skills?.length ?? 0} total</span>
          </div>

          <div className="space-y-1.5">
            {(bundle.skills ?? []).map((skill, i) => (
              <SkillRow
                key={skill.id}
                skill={skill}
                index={i}
                expanded={expanded.has(skill.id)}
                onToggle={() => toggle(skill.id)}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function SkillRow({ skill, index, expanded, onToggle }: { skill: Skill; index: number; expanded: boolean; onToggle: () => void }) {
  const dotColor = SKILL_CAT_COLORS[skill.primary_category] ?? "rgba(255,255,255,0.3)";

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: index * 0.025 }}
      className="rounded-xl border border-white/[0.07] bg-white/[0.025] overflow-hidden"
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-white/[0.04] transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ background: dotColor }} />
          <div className="min-w-0">
            <div className="text-sm font-medium text-white/90">{skill.name}</div>
            <div className="font-mono text-[11px] text-white/25 mt-0.5">{skill.slug}</div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-4">
          <span className="flex items-center gap-1 text-[11px] text-white/25 hidden sm:flex">
            <Star size={10} className="text-yellow-400/50" /> {skill.quality_score.toFixed(1)}
          </span>
          {expanded ? (
            <CaretUp size={13} className="text-white/25" />
          ) : (
            <CaretDown size={13} className="text-white/25" />
          )}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-white/[0.06]">
              <p className="text-sm text-white/45 mt-3 mb-3 leading-relaxed">
                {skill.description || "No description available."}
              </p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {skill.tags.slice(0, 8).map((tag) => (
                  <span key={tag} className="text-[11px] text-white/32 bg-white/[0.05] rounded-md px-2 py-0.5">
                    {tag}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                <code className="text-[12px] text-green-400 font-mono bg-black/35 rounded-lg px-3 py-1.5">
                  {skill.install_command}
                </code>
                {skill.source_url && (
                  <a
                    href={skill.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-white/28 hover:text-white/55 flex items-center gap-1 transition-colors"
                  >
                    <ArrowSquareOut size={11} /> Source
                  </a>
                )}
                <Link
                  href={`/skills/${skill.slug}`}
                  className="text-xs text-white/28 hover:text-white/55 transition-colors ml-auto"
                >
                  View detail →
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function Spinner({ label }: { label: string }) {
  return (
    <div className="min-h-screen bg-[#060606] text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-white/15 border-t-violet-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white/35 text-sm font-mono">{label}</p>
      </div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="min-h-screen bg-[#060606] text-white flex items-center justify-center">
      <div className="text-center">
        <p className="text-white/40 mb-4 text-lg">Bundle not found.</p>
        <Link href="/" className="text-sm text-violet-400 hover:underline font-mono">← Go home</Link>
      </div>
    </div>
  );
}
