"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MagnifyingGlass, ArrowRight, Star, DownloadSimple, ArrowSquareOut, Heart } from "@phosphor-icons/react";
import BundleCard from "@/components/BundleCard";
import Navbar from "@/components/Navbar";
import { api, type Bundle, type Skill } from "@/lib/api";
import Link from "next/link";
import { useSession } from "next-auth/react";

const TYPES = ["All", "role", "task", "micro"];

const CAT_COLORS: Record<string, string> = {
  frontend: "#60a5fa", backend: "#4ade80", fullstack: "#c084fc",
  devops: "#fb923c", "ml-ai": "#f472b6", security: "#f87171",
  database: "#22d3ee", testing: "#facc15", cloud: "#38bdf8",
  mobile: "#818cf8", "data-science": "#a3e635",
};

const tabVariants = {
  hidden: { opacity: 0, y: 8 },
  show:   { opacity: 1, y: 0 },
  exit:   { opacity: 0, y: -8 },
};

const PAGE_SIZE = 50;

function getPageNumbers(current: number, totalPages: number): (number | "…")[] {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
  if (current <= 4)  return [1, 2, 3, 4, 5, "…", totalPages];
  if (current >= totalPages - 3) return [1, "…", totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  return [1, "…", current - 1, current, current + 1, "…", totalPages];
}

export default function ExplorePage() {
  const { data: session } = useSession();
  const [bundles, setBundles]         = useState<Bundle[]>([]);
  const [skills, setSkills]           = useState<Skill[]>([]);
  const [total, setTotal]             = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loadingPage, setLoadingPage] = useState(false);
  const [query, setQuery]             = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [activeType, setActiveType]   = useState("All");
  const [tab, setTab]                 = useState<"bundles" | "skills">("bundles");
  const [searching, setSearching]     = useState(false);
  const [loadingBundles, setLoadingBundles] = useState(true);
  const [loadingSkills, setLoadingSkills]   = useState(true);
  const [savedSkillIds, setSavedSkillIds]   = useState<Set<number>>(new Set());
  const [savedBundleIds, setSavedBundleIds] = useState<Set<number>>(new Set());
  const [saving, setSaving]           = useState<Set<string>>(new Set());
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadPage = async (page: number, isInitial = false) => {
    if (isInitial) setLoadingSkills(true);
    else setLoadingPage(true);
    try {
      const res = await api.skills.list({ limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });
      const items: Skill[] = Array.isArray(res) ? (res as unknown as Skill[]) : (res.items ?? []);
      const tot: number    = Array.isArray(res) ? items.length : (res.total ?? 0);
      setSkills(items);
      setTotal(tot);
      setCurrentPage(page);
    } catch { /* ignore */ }
    finally { setLoadingSkills(false); setLoadingPage(false); }
  };

  useEffect(() => {
    Promise.all([
      api.bundles.list()
        .then((b) => { setBundles(b); setLoadingBundles(false); })
        .catch(() => { setLoadingBundles(false); }),
      loadPage(1, true),
    ]);

    // Load saved items if logged in
    if (session) {
      api.user.saves.list(session)
        .then((data) => {
          setSavedSkillIds(new Set(data.saved_skill_ids));
          setSavedBundleIds(new Set(data.saved_bundle_ids));
        })
        .catch(() => {});
    }
  }, [session]);

  const handleSearch = (q: string) => {
    setQuery(q);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!q.trim() || q.length < 2) {
      setIsSearching(false);
      setSearching(false);
      loadPage(1, true);
      return;
    }
    setSearching(true);
    searchTimer.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const result = await api.search.skills(q);
        setSkills(result.results);
        setTotal(result.results.length);
        setCurrentPage(1);
        setTab("skills");
      } catch { /* ignore */ }
      finally { setSearching(false); }
    }, 300);
  };

  const handleSaveSkill = async (skillId: number) => {
    if (!session) return;
    const key = `skill-${skillId}`;
    setSaving((prev) => new Set(prev).add(key));
    try {
      if (savedSkillIds.has(skillId)) {
        await api.user.saves.unsaveSkill(skillId, session);
        setSavedSkillIds((prev) => {
          const next = new Set(prev);
          next.delete(skillId);
          return next;
        });
      } else {
        await api.user.saves.saveSkill(skillId, session);
        setSavedSkillIds((prev) => new Set(prev).add(skillId));
      }
    } catch { /* ignore */ }
    finally { setSaving((prev) => { const next = new Set(prev); next.delete(key); return next; }); }
  };

  const handleSaveBundle = async (bundleId: number) => {
    if (!session) return;
    const key = `bundle-${bundleId}`;
    setSaving((prev) => new Set(prev).add(key));
    try {
      if (savedBundleIds.has(bundleId)) {
        await api.user.saves.unsaveBundle(bundleId, session);
        setSavedBundleIds((prev) => {
          const next = new Set(prev);
          next.delete(bundleId);
          return next;
        });
      } else {
        await api.user.saves.saveBundle(bundleId, session);
        setSavedBundleIds((prev) => new Set(prev).add(bundleId));
      }
    } catch { /* ignore */ }
    finally { setSaving((prev) => { const next = new Set(prev); next.delete(key); return next; }); }
  };

  const filteredBundles = bundles.filter((b) => activeType === "All" || b.type === activeType);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 70% 40% at 50% -10%, rgba(124,58,237,0.09) 0%, transparent 60%)" }}
      />

      <Navbar />

      <div className="relative max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-10"
        >
          <h1 className="text-4xl font-bold mb-2">Explore</h1>
          <p className="text-white/38">Browse all bundles and skills across every AI platform.</p>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.06 }}
          className="relative mb-8"
        >
          <div className="relative">
            <div className="relative flex items-center rounded-xl border border-white/10 bg-white/[0.04] hover:border-white/20 hover:bg-white/[0.06] focus-within:border-violet-500/50 focus-within:bg-white/[0.05] focus-within:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] transition-all duration-200">
              <MagnifyingGlass size={16} className="absolute left-4 text-white/28" />
              <input
                type="text"
                placeholder="Search skills by name, tag, or role..."
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full bg-transparent pl-10 pr-12 py-3.5 text-sm outline-none placeholder:text-white/22"
              />
              {searching ? (
                <div className="absolute right-4">
                  <div className="w-4 h-4 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
                </div>
              ) : query && (
                <button
                  onClick={() => handleSearch("")}
                  className="absolute right-4 text-white/25 hover:text-white/50 transition-colors text-lg leading-none"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex items-center gap-1 mb-8 border-b border-white/[0.07]"
        >
          {(["bundles", "skills"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
                tab === t ? "text-white" : "text-white/38 hover:text-white/65"
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
              <span className="ml-2 font-mono text-xs text-white/22">
                {t === "bundles"
                ? (loadingBundles ? "…" : filteredBundles.length)
                : (loadingSkills  ? "…" : (total || skills.length))}
              </span>
              {tab === t && (
                <motion.div
                  layoutId="tab-underline"
                  className="absolute bottom-0 left-0 right-0 h-px bg-violet-500"
                />
              )}
            </button>
          ))}
        </motion.div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {tab === "bundles" ? (
            <motion.div key="bundles" variants={tabVariants} initial="hidden" animate="show" exit="exit">
              {/* Type filters */}
              <div className="flex gap-2 mb-6 flex-wrap">
                {TYPES.map((type) => (
                  <button
                    key={type}
                    onClick={() => setActiveType(type)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border"
                    style={{
                      background: activeType === type ? "rgba(124,58,237,0.12)" : "rgba(255,255,255,0.03)",
                      borderColor: activeType === type ? "rgba(124,58,237,0.35)" : "rgba(255,255,255,0.08)",
                      color: activeType === type ? "#c084fc" : "rgba(255,255,255,0.38)",
                    }}
                  >
                    {type}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {loadingBundles ? (
                  Array.from({ length: 9 }).map((_, i) => (
                    <div key={i} className="h-36 rounded-2xl border border-white/[0.07] bg-white/[0.03] animate-pulse" />
                  ))
                ) : filteredBundles.length > 0 ? (
                  filteredBundles.map((b, i) => (
                    <motion.div
                      key={b.slug}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.04 }}
                    >
                      <BundleCard 
                        bundle={b}
                        isSaved={savedBundleIds.has(b.id)}
                        onSave={() => handleSaveBundle(b.id)}
                        isLoading={saving.has(`bundle-${b.id}`)}
                      />
                    </motion.div>
                  ))
                ) : (
                  <p className="col-span-3 text-center py-16 text-white/28 text-sm">No bundles found.</p>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div key="skills" variants={tabVariants} initial="hidden" animate="show" exit="exit">
              <div className="space-y-1.5">
                {loadingSkills ? (
                  Array.from({ length: 12 }).map((_, i) => (
                    <div key={i} className="h-14 rounded-xl border border-white/[0.07] bg-white/[0.025] animate-pulse" />
                  ))
                ) : skills.length === 0 ? (
                  <p className="text-center py-16 text-white/28 text-sm">No skills found.</p>
                ) : skills.map((s, i) => {
                  const catColor = CAT_COLORS[s.primary_category] ?? "rgba(255,255,255,0.4)";
                  return (
                    <motion.div
                      key={s.slug}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.25, delay: i * 0.025 }}
                    >
                      <div className="flex items-center justify-between">
                        <Link href={`/skills/${s.slug}`} className="flex-1">
                          <motion.div
                            whileHover={{ x: 3 }}
                            transition={{ duration: 0.15 }}
                            className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.025] px-4 py-3.5 hover:border-white/14 hover:bg-white/[0.04] transition-colors cursor-pointer group"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span
                                className="w-2 h-2 rounded-full shrink-0"
                                style={{ background: catColor }}
                              />
                              <div className="min-w-0">
                                <div className="text-sm font-medium text-white/90 group-hover:text-white transition-colors">
                                  {s.name}
                                </div>
                                <div className="text-xs text-white/32 truncate max-w-md mt-0.5">
                                  {s.description}
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-4 shrink-0 ml-6">
                              <span
                                className="text-[11px] font-medium hidden sm:block"
                                style={{ color: catColor }}
                              >
                                {s.primary_category}
                              </span>
                              <div className="flex items-center gap-1 text-[11px] text-white/25 hidden md:flex">
                                <Star size={10} className="text-yellow-400/50" />
                                {s.quality_score.toFixed(1)}
                              </div>
                              <code className="text-[11px] text-green-400/60 font-mono bg-black/30 rounded px-2 py-0.5 hidden lg:block">
                                {s.install_command?.split(" ").slice(0, 4).join(" ")}…
                              </code>
                              <ArrowRight size={13} className="text-white/15 group-hover:text-white/40 transition-colors" />
                            </div>
                          </motion.div>
                        </Link>
                        
                        {session && (
                          <button
                            onClick={() => handleSaveSkill(s.id)}
                            disabled={saving.has(`skill-${s.id}`)}
                            className="ml-3 p-2 rounded-lg hover:bg-white/[0.06] transition-colors disabled:opacity-50"
                          >
                            <Heart 
                              size={16} 
                              weight={savedSkillIds.has(s.id) ? "fill" : "regular"}
                              className={savedSkillIds.has(s.id) ? "text-red-400" : "text-white/30"}
                            />
                          </button>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {!isSearching && totalPages > 1 && (
                <div className="flex items-center justify-center gap-1 mt-8">
                  <button
                    onClick={() => loadPage(currentPage - 1)}
                    disabled={currentPage === 1 || loadingPage}
                    className="px-3 py-1.5 rounded-lg text-sm text-white/40 hover:text-white hover:bg-white/[0.06] disabled:opacity-25 disabled:cursor-not-allowed transition-all"
                  >
                    ←
                  </button>

                  {getPageNumbers(currentPage, totalPages).map((p, i) =>
                    p === "…" ? (
                      <span key={`ellipsis-${i}`} className="px-2 text-white/20 text-sm select-none">…</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => loadPage(p as number)}
                        disabled={loadingPage}
                        className={`min-w-[32px] px-2 py-1.5 rounded-lg text-sm font-medium transition-all ${
                          currentPage === p
                            ? "bg-violet-600/20 border border-violet-500/40 text-violet-300"
                            : "text-white/40 hover:text-white hover:bg-white/[0.06]"
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )}

                  <button
                    onClick={() => loadPage(currentPage + 1)}
                    disabled={currentPage === totalPages || loadingPage}
                    className="px-3 py-1.5 rounded-lg text-sm text-white/40 hover:text-white hover:bg-white/[0.06] disabled:opacity-25 disabled:cursor-not-allowed transition-all"
                  >
                    →
                  </button>

                  <span className="ml-3 text-xs text-white/20 font-mono">
                    {((currentPage - 1) * PAGE_SIZE) + 1}–{Math.min(currentPage * PAGE_SIZE, total)} of {total}
                  </span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
