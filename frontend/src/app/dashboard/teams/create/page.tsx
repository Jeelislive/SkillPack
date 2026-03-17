"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, ArrowLeft, Check } from "@phosphor-icons/react";
import Link from "next/link";
import { api } from "@/lib/api";
import Logo from "@/components/Logo";

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };

export default function CreateTeamPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    // Generate slug from name
    const generated = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 20);
    setSlug(generated);
  }, [name]);

  const handleCreate = async () => {
    if (!session || !name.trim()) return;
    setCreating(true);
    setError("");
    try {
      const team = await api.teams.create({ name, slug: slug || undefined }, session);
      router.push(`/dashboard/teams/${team.slug}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create team");
      setCreating(false);
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-[#060606] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (!session) return null;

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div className="fixed inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 80% 45% at 50% -5%, rgba(124,58,237,0.11) 0%, transparent 65%)" }} />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard/teams" className="flex items-center gap-2.5">
            <Logo />
            <span className="font-bold tracking-tight">Create Team</span>
          </Link>
          <Link href="/dashboard/teams" className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
            <ArrowLeft size={14} /> Teams
          </Link>
        </div>
      </nav>

      <main className="relative z-10 max-w-3xl mx-auto px-6 pt-10 pb-24">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          
          {/* Header */}
          <motion.div variants={fadeUp} className="mb-8">
            <h1 className="text-2xl font-bold text-white/90 mb-2">Create Team</h1>
            <p className="text-sm text-white/40">
              Set up a collaborative workspace for your team to share and manage skill bundles.
            </p>
          </motion.div>

          {/* Form */}
          <motion.div variants={fadeUp} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Team Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Engineering Team, Design Squad"
                className="w-full px-4 py-3 rounded-xl border border-white/[0.08] bg-white/[0.02] text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 focus:bg-white/[0.04] transition-colors"
                disabled={creating}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Team URL Slug
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-4 text-white/30 text-sm">
                  skillpack.app/teams/
                </div>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="team-name"
                  className="w-full pl-32 pr-4 py-3 rounded-xl border border-white/[0.08] bg-white/[0.02] text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 focus:bg-white/[0.04] transition-colors font-mono text-sm"
                  disabled={creating}
                />
              </div>
              <p className="text-xs text-white/25 mt-1">
                Only letters, numbers, and hyphens. Auto-generated from name.
              </p>
            </div>

            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Link
                href="/dashboard/teams"
                className="px-6 py-3 rounded-xl border border-white/[0.08] text-white/60 hover:text-white hover:bg-white/[0.04] transition-colors"
              >
                Cancel
              </Link>
              <button
                onClick={handleCreate}
                disabled={!name.trim() || creating}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-violet-600 text-white font-medium hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {creating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus size={16} />
                    Create Team
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      </main>
    </div>
  );
}
