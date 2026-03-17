"use client";

import { useSession, signOut } from "next-auth/react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { SignOut, Package, Star, Plus, Trash, Globe, Lock, Users } from "@phosphor-icons/react";
import Link from "next/link";
import Image from "next/image";
import { api, type Bundle, type Skill } from "@/lib/api";
import Logo from "@/components/Logo";

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [myBundles, setMyBundles]     = useState<Bundle[]>([]);
  const [savedSkills, setSavedSkills] = useState<Skill[]>([]);
  const [savedBundles, setSavedBundles] = useState<Bundle[]>([]);
  const [loadingBundles, setLoadingBundles]   = useState(true);
  const [loadingSaves, setLoadingSaves]       = useState(true);
  const [deletingSlug, setDeletingSlug]       = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (!session) return;
    api.user.bundles.list(session)
      .then(setMyBundles)
      .catch(() => {})
      .finally(() => setLoadingBundles(false));

    api.user.saves.list(session)
      .then((data) => { setSavedSkills(data.skills); setSavedBundles(data.bundles); })
      .catch(() => {})
      .finally(() => setLoadingSaves(false));
  }, [session]);

  const handleDelete = async (slug: string) => {
    if (!session || !confirm("Delete this bundle?")) return;
    setDeletingSlug(slug);
    try {
      await api.user.bundles.delete(slug, session);
      setMyBundles((prev) => prev.filter((b) => b.slug !== slug));
    } catch { /* ignore */ }
    finally { setDeletingSlug(null); }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-[#060606] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (!session) return null;

  const user = session.user;

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div className="fixed inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 80% 45% at 50% -5%, rgba(124,58,237,0.11) 0%, transparent 65%)" }} />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <Logo />
            <span className="font-bold tracking-tight">SkillPack</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/dashboard/teams" className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
              <Users size={15} /> Teams
            </Link>
            <button
              onClick={() => signOut({ callbackUrl: "/" })}
              className="flex items-center gap-2 text-sm text-white/40 hover:text-white/80 transition-colors"
            >
              <SignOut size={15} /> Sign out
            </button>
          </div>
        </div>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-14 pb-24">
        <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-10">

          {/* Profile card */}
          <motion.div variants={fadeUp} className="rounded-3xl border border-white/[0.08] bg-white/[0.03] backdrop-blur p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6">
            {user.image ? (
              <Image src={user.image} alt={user.name ?? "Avatar"} width={72} height={72} className="rounded-2xl ring-2 ring-violet-500/30 shrink-0" />
            ) : (
              <div className="w-[72px] h-[72px] rounded-2xl bg-violet-700/30 flex items-center justify-center shrink-0">
                <span className="text-2xl font-bold text-violet-300">{user.name?.[0] ?? "?"}</span>
              </div>
            )}
            <div className="text-center sm:text-left">
              <h1 className="text-xl font-bold">{user.name}</h1>
              {user.email && <p className="text-sm text-white/40 mt-0.5">{user.email}</p>}
              <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-violet-300/80 border border-violet-500/20 rounded-full px-3 py-1 bg-violet-500/5">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                Free plan
              </div>
            </div>
          </motion.div>

          {/* My Bundles */}
          <motion.div variants={fadeUp}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white/80">My Bundles</h2>
              <Link
                href="/dashboard/create-bundle"
                className="flex items-center gap-1.5 text-xs font-medium text-violet-400 border border-violet-500/25 rounded-lg px-3 py-1.5 bg-violet-500/5 hover:bg-violet-500/10 transition-colors"
              >
                <Plus size={13} /> Create Bundle
              </Link>
            </div>

            {loadingBundles ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => <div key={i} className="h-16 rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse" />)}
              </div>
            ) : myBundles.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.10)", border: "1px solid rgba(124,58,237,0.18)" }}>
                  <Package size={20} className="text-violet-400" />
                </div>
                <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                  No bundles yet. Create your first bundle to share your favorite skills.
                </p>
                <Link href="/dashboard/create-bundle" className="text-xs text-violet-400/70 hover:text-violet-400 transition-colors border border-violet-500/20 rounded-lg px-4 py-2 bg-violet-500/5 hover:bg-violet-500/10">
                  + Create your first bundle
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {myBundles.map((b) => (
                  <div key={b.slug} className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.025] px-4 py-3 hover:border-white/12 transition-colors group">
                    <Link href={`/bundle/${b.slug}`} className="flex items-center gap-3 min-w-0 flex-1">
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-white/90">{b.name}</div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[11px] text-white/30 font-mono">{b.skill_count} skills</span>
                          <span className="flex items-center gap-1 text-[11px] text-white/25">
                            {b.is_public ? <Globe size={10} /> : <Lock size={10} />}
                            {b.is_public ? "Public" : "Private"}
                          </span>
                        </div>
                      </div>
                    </Link>
                    <button
                      onClick={() => handleDelete(b.slug)}
                      disabled={deletingSlug === b.slug}
                      className="opacity-0 group-hover:opacity-100 ml-3 p-1.5 rounded-lg hover:bg-red-500/15 text-white/25 hover:text-red-400 transition-all disabled:opacity-50"
                    >
                      <Trash size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Saved Skills */}
          <motion.div variants={fadeUp}>
            <h2 className="text-lg font-semibold mb-4 text-white/80">Saved Skills</h2>
            {loadingSaves ? (
              <div className="space-y-2">{[0,1,2].map((i) => <div key={i} className="h-14 rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse" />)}</div>
            ) : savedSkills.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.10)", border: "1px solid rgba(124,58,237,0.18)" }}>
                  <Star size={20} className="text-violet-400" />
                </div>
                <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                  Heart skills on the explore page to save them here.
                </p>
                <Link href="/explore" className="text-xs text-violet-400/70 hover:text-violet-400 transition-colors border border-violet-500/20 rounded-lg px-4 py-2 bg-violet-500/5 hover:bg-violet-500/10">
                  Explore skills
                </Link>
              </div>
            ) : (
              <div className="space-y-1.5">
                {savedSkills.map((s) => (
                  <Link key={s.id} href={`/skills/${s.slug}`}>
                    <div className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.025] px-4 py-3 hover:border-white/12 transition-colors">
                      <div className="text-sm font-medium text-white/80">{s.name}</div>
                      <span className="text-xs text-white/30 font-mono">{s.primary_category}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </motion.div>

          {/* Saved Bundles */}
          <motion.div variants={fadeUp}>
            <h2 className="text-lg font-semibold mb-4 text-white/80">Saved Bundles</h2>
            {loadingSaves ? (
              <div className="space-y-2">{[0,1].map((i) => <div key={i} className="h-14 rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse" />)}</div>
            ) : savedBundles.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(59,130,246,0.10)", border: "1px solid rgba(59,130,246,0.18)" }}>
                  <Package size={20} className="text-blue-400" />
                </div>
                <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                  Heart bundles on the explore page to save them here.
                </p>
                <Link href="/explore" className="text-xs text-blue-400/70 hover:text-blue-400 transition-colors border border-blue-500/20 rounded-lg px-4 py-2 bg-blue-500/5 hover:bg-blue-500/10">
                  Browse bundles
                </Link>
              </div>
            ) : (
              <div className="space-y-1.5">
                {savedBundles.map((b) => (
                  <Link key={b.id} href={`/bundle/${b.slug}`}>
                    <div className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.025] px-4 py-3 hover:border-white/12 transition-colors">
                      <div className="text-sm font-medium text-white/80">{b.name}</div>
                      <span className="text-xs text-white/30 font-mono">{b.skill_count} skills</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </motion.div>

        </motion.div>
      </main>
    </div>
  );
}
