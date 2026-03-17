"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Users, Plus, ArrowLeft, ArrowRight, UserCheck, UserList, Shield } from "@phosphor-icons/react";
import Link from "next/link";
import { api, type Team } from "@/lib/api";

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function TeamsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (!session) return;
    api.teams.list(session)
      .then(setTeams)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session]);

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
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-700 flex items-center justify-center shadow-lg shadow-violet-950/50">
              <Users size={14} className="text-white" />
            </div>
            <span className="font-bold tracking-tight">Teams</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard/teams/create"
              className="flex items-center gap-1.5 text-xs font-medium text-violet-400 border border-violet-500/25 rounded-lg px-3 py-1.5 bg-violet-500/5 hover:bg-violet-500/10 transition-colors"
            >
              <Plus size={13} /> Create Team
            </Link>
            <Link href="/dashboard" className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
              <ArrowLeft size={14} /> Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-14 pb-24">
        <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-10">

          {/* Header */}
          <motion.div variants={fadeUp}>
            <h1 className="text-2xl font-bold text-white/90 mb-2">Team Workspaces</h1>
            <p className="text-sm text-white/40">
              Collaborate with your team on shared skill bundles and track installations.
            </p>
          </motion.div>

          {/* Teams List */}
          <motion.div variants={fadeUp}>
            {loading ? (
              <div className="space-y-3">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-20 rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse" />
                ))}
              </div>
            ) : teams.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.10)", border: "1px solid rgba(124,58,237,0.18)" }}>
                  <Users size={20} className="text-violet-400" />
                </div>
                <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                  No teams yet. Create your first team to collaborate with colleagues.
                </p>
                <Link href="/dashboard/teams/create" className="text-xs text-violet-400/70 hover:text-violet-400 transition-colors border border-violet-500/20 rounded-lg px-4 py-2 bg-violet-500/5 hover:bg-violet-500/10">
                  + Create your first team
                </Link>
              </div>
            ) : (
              <div className="grid gap-4">
                {teams.map((team) => (
                  <Link key={team.slug} href={`/dashboard/teams/${team.slug}`}>
                    <motion.div
                      whileHover={{ x: 3 }}
                      className="flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.025] px-6 py-4 hover:border-white/12 transition-colors group"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-violet-700/20 flex items-center justify-center">
                          <Users size={18} className="text-violet-400" />
                        </div>
                        <div>
                          <h3 className="font-medium text-white/90">{team.name}</h3>
                          <p className="text-xs text-white/40 mt-0.5">
                            {team.slug} • {team.members?.length || 0} members
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {team.canonical_bundle_id && (
                          <div className="flex items-center gap-1 text-xs text-violet-300/70">
                            <Shield size={12} />
                            Canonical bundle set
                          </div>
                        )}
                        <ArrowRight size={16} className="text-white/20 group-hover:text-white/40 transition-colors" />
                      </div>
                    </motion.div>
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
