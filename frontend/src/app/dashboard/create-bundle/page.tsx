"use client";

import { useState, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { MagnifyingGlass, Check, Lock, Globe, ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import Link from "next/link";
import { api, type Skill } from "@/lib/api";
import Logo from "@/components/Logo";

const STEPS = ["Info", "Skills", "Settings"];

export default function CreateBundlePage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [step, setStep]           = useState(0);
  const [name, setName]           = useState("");
  const [description, setDesc]    = useState("");
  const [isPublic, setIsPublic]   = useState(true);
  const [selectedIds, setSelected] = useState<Set<number>>(new Set());
  const [skills, setSkills]       = useState<Skill[]>([]);
  const [query, setQuery]         = useState("");
  const [searching, setSearching] = useState(false);
  const [creating, setCreating]   = useState(false);
  const [error, setError]         = useState("");
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    api.skills.list({ limit: 20 }).then((res) => {
      setSkills(Array.isArray(res) ? (res as unknown as Skill[]) : (res.items ?? []));
    }).catch(() => {});
  }, []);

  const handleSearch = (q: string) => {
    setQuery(q);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!q.trim() || q.length < 2) { setSearching(false); return; }
    setSearching(true);
    searchTimer.current = setTimeout(async () => {
      try {
        const result = await api.search.skills(q);
        setSkills(result.results);
      } catch { /* ignore */ }
      finally { setSearching(false); }
    }, 300);
  };

  const toggleSkill = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleCreate = async () => {
    if (!session) return;
    setCreating(true);
    setError("");
    try {
      const bundle = await api.user.bundles.create(
        { name, description, skill_ids: [...selectedIds], is_public: isPublic },
        session,
      );
      router.push(`/bundle/${bundle.slug}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create bundle");
      setCreating(false);
    }
  };

  if (status === "loading") return <LoadingSpinner />;
  if (!session) return null;

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <Logo />
            <span className="font-bold tracking-tight">SkillPack</span>
          </Link>
          <Link href="/dashboard" className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
            <ArrowLeft size={14} /> Dashboard
          </Link>
        </div>
      </nav>

      <main className="relative z-10 max-w-3xl mx-auto px-6 pt-10 pb-24">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          <h1 className="text-2xl font-bold mb-2">Create Bundle</h1>
          <p className="text-white/38 text-sm mb-8">Curate your own skill bundle and share it with your team.</p>

          {/* Step indicators */}
          <div className="flex items-center gap-2 mb-10">
            {STEPS.map((s, i) => (
              <div key={s} className="flex items-center gap-2">
                <button
                  onClick={() => i < step && setStep(i)}
                  className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                    i === step ? "text-violet-300" : i < step ? "text-white/50 hover:text-white/70" : "text-white/20"
                  }`}
                >
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border transition-colors ${
                    i < step ? "bg-violet-600/30 border-violet-500/40 text-violet-300" :
                    i === step ? "bg-violet-600/20 border-violet-500/50 text-violet-300" :
                    "border-white/10 text-white/20"
                  }`}>
                    {i < step ? <Check size={10} weight="bold" /> : i + 1}
                  </span>
                  {s}
                </button>
                {i < STEPS.length - 1 && <div className="w-8 h-px bg-white/10" />}
              </div>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {/* Step 0 - Info */}
            {step === 0 && (
              <motion.div key="info" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-white/60 mb-2">Bundle name *</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="My Full-Stack Bundle"
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-violet-500/50 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] transition-all placeholder:text-white/20"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white/60 mb-2">Description</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDesc(e.target.value)}
                      placeholder="What makes this bundle special..."
                      rows={3}
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-violet-500/50 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] transition-all placeholder:text-white/20 resize-none"
                    />
                  </div>
                </div>
                <div className="mt-8 flex justify-end">
                  <button
                    onClick={() => setStep(1)}
                    disabled={!name.trim()}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium transition-colors"
                  >
                    Next: Pick Skills <ArrowRight size={14} />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 1 - Skills */}
            {step === 1 && (
              <motion.div key="skills" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
                <div className="relative mb-4">
                  <MagnifyingGlass size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/28" />
                  <input
                    type="text"
                    placeholder="Search skills..."
                    value={query}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl pl-9 pr-4 py-3 text-sm outline-none focus:border-violet-500/50 transition-all placeholder:text-white/20"
                  />
                  {searching && (
                    <div className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
                  )}
                </div>

                {selectedIds.size > 0 && (
                  <p className="text-xs text-violet-300/70 mb-3">{selectedIds.size} skill{selectedIds.size !== 1 ? "s" : ""} selected</p>
                )}

                <div className="space-y-1 max-h-[400px] overflow-y-auto pr-1">
                  {skills.map((s) => {
                    const sel = selectedIds.has(s.id);
                    return (
                      <button
                        key={s.id}
                        onClick={() => toggleSkill(s.id)}
                        className={`w-full flex items-center justify-between rounded-xl border px-4 py-3 text-left transition-all ${
                          sel ? "border-violet-500/40 bg-violet-500/10" : "border-white/[0.07] bg-white/[0.025] hover:border-white/14"
                        }`}
                      >
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-white/90 truncate">{s.name}</div>
                          <div className="text-xs text-white/32 truncate">{s.description}</div>
                        </div>
                        <div className={`ml-3 w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center transition-colors ${
                          sel ? "border-violet-400 bg-violet-500" : "border-white/20"
                        }`}>
                          {sel && <Check size={10} weight="bold" className="text-white" />}
                        </div>
                      </button>
                    );
                  })}
                </div>

                <div className="mt-6 flex justify-between">
                  <button onClick={() => setStep(0)} className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
                    <ArrowLeft size={14} /> Back
                  </button>
                  <button
                    onClick={() => setStep(2)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-sm font-medium transition-colors"
                  >
                    Next: Settings <ArrowRight size={14} />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 2 - Settings */}
            {step === 2 && (
              <motion.div key="settings" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
                <div className="space-y-4">
                  {[
                    { value: true,  Icon: Globe, label: "Public",  desc: "Visible to everyone on the explore page" },
                    { value: false, Icon: Lock,  label: "Private", desc: "Only visible to you (Free: max 3 private)" },
                  ].map(({ value, Icon, label, desc }) => (
                    <button
                      key={label}
                      onClick={() => setIsPublic(value)}
                      className={`w-full flex items-center gap-4 rounded-xl border px-5 py-4 text-left transition-all ${
                        isPublic === value ? "border-violet-500/40 bg-violet-500/10" : "border-white/[0.08] bg-white/[0.025] hover:border-white/15"
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                        isPublic === value ? "bg-violet-500/20" : "bg-white/[0.05]"
                      }`}>
                        <Icon size={18} className={isPublic === value ? "text-violet-300" : "text-white/40"} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white/90">{label}</div>
                        <div className="text-xs text-white/38">{desc}</div>
                      </div>
                      {isPublic === value && (
                        <Check size={16} className="ml-auto text-violet-400 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>

                <div className="mt-6 p-4 rounded-xl border border-white/[0.06] bg-white/[0.02]">
                  <p className="text-xs text-white/40 mb-1">Summary</p>
                  <p className="text-sm font-medium text-white/80">{name}</p>
                  <p className="text-xs text-white/35 mt-0.5">
                    {selectedIds.size} skill{selectedIds.size !== 1 ? "s" : ""} · {isPublic ? "Public" : "Private"}
                  </p>
                </div>

                {error && (
                  <p className="mt-3 text-sm text-red-400/80 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
                    {error}
                  </p>
                )}

                <div className="mt-6 flex justify-between">
                  <button onClick={() => setStep(1)} className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
                    <ArrowLeft size={14} /> Back
                  </button>
                  <button
                    onClick={handleCreate}
                    disabled={creating}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-60 disabled:cursor-not-allowed text-sm font-semibold transition-colors"
                  >
                    {creating ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Creating…
                      </>
                    ) : "Create Bundle"}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </main>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-[#060606] flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
    </div>
  );
}
