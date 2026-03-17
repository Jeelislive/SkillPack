"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Users, ArrowLeft, Plus, Shield, Copy, UserCheck, User, Envelope } from "@phosphor-icons/react";
import Link from "next/link";
import { api, type Team, type Bundle } from "@/lib/api";

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } } };

export default function TeamPage({ params }: { params: { slug: string } }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [team, setTeam] = useState<Team | null>(null);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (!session || !params.slug) return;
    
    Promise.all([
      api.teams.get(params.slug, session),
      api.bundles.list()
    ]).then(([teamData, allBundles]) => {
      setTeam(teamData);
      // Filter user's bundles for canonical selection
      const userBundles = allBundles.filter(b => b.owner_user_id === session.user.id);
      setBundles(userBundles);
    }).catch(() => {
      router.push("/dashboard/teams");
    }).finally(() => setLoading(false));
  }, [session, params.slug, router]);

  const handleInvite = async () => {
    if (!session || !team || !inviteEmail.trim()) return;
    setInviting(true);
    setError("");
    try {
      await api.teams.inviteMember(team.slug, inviteEmail, session);
      setInviteEmail("");
      // Refresh team data
      const updated = await api.teams.get(team.slug, session);
      setTeam(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to invite member");
    } finally {
      setInviting(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!session || !team || !confirm("Remove this member from the team?")) return;
    try {
      await api.teams.removeMember(team.slug, userId, session);
      // Refresh team data
      const updated = await api.teams.get(team.slug, session);
      setTeam(updated);
    } catch { /* ignore */ }
  };

  const handleSetCanonical = async (bundleId: number) => {
    if (!session || !team) return;
    try {
      await api.teams.setCanonical(team.slug, bundleId, session);
      // Refresh team data
      const updated = await api.teams.get(team.slug, session);
      setTeam(updated);
    } catch { /* ignore */ }
  };

  const copyInstallCommand = () => {
    if (!team) return;
    api.teams.installCommand(team.slug).then(({ command }) => {
      navigator.clipboard.writeText(command);
    });
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-[#060606] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (!session || !team) return null;

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div className="fixed inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 80% 45% at 50% -5%, rgba(124,58,237,0.11) 0%, transparent 65%)" }} />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard/teams" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-700 flex items-center justify-center">
              <Users size={14} className="text-white" />
            </div>
            <span className="font-bold tracking-tight">{team.name}</span>
          </Link>
          <div className="flex items-center gap-3">
            <button
              onClick={copyInstallCommand}
              className="flex items-center gap-1.5 text-xs font-medium text-violet-400 border border-violet-500/25 rounded-lg px-3 py-1.5 bg-violet-500/5 hover:bg-violet-500/10 transition-colors"
            >
              <Copy size={13} /> Copy Install Command
            </button>
            <Link href="/dashboard/teams" className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors">
              <ArrowLeft size={14} /> Teams
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-14 pb-24">
        <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-10">

          {/* Team Info */}
          <motion.div variants={fadeUp} className="rounded-3xl border border-white/[0.08] bg-white/[0.03] backdrop-blur p-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-white/90 mb-2">{team.name}</h1>
                <p className="text-sm text-white/40">Team workspace • {team.slug}</p>
              </div>
              {team.canonical_bundle_id && (
                <div className="flex items-center gap-2 text-xs text-violet-300/70 border border-violet-500/20 rounded-full px-3 py-1 bg-violet-500/5">
                  <Shield size={10} />
                  Canonical bundle set
                </div>
              )}
            </div>

            {/* Canonical Bundle */}
            <div className="border-t border-white/[0.06] pt-6">
              <h3 className="text-sm font-medium text-white/70 mb-3">Canonical Bundle</h3>
              {team.canonical_bundle_id ? (
                <div className="flex items-center justify-between p-3 rounded-lg border border-white/[0.06] bg-white/[0.02]">
                  <span className="text-sm text-white/60">Bundle ID: {team.canonical_bundle_id}</span>
                  <button
                    onClick={() => handleSetCanonical(0)}
                    className="text-xs text-red-400/70 hover:text-red-400 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-white/35">Set a canonical bundle for team installations</p>
                  <select
                    onChange={(e) => handleSetCanonical(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-white/[0.08] bg-white/[0.02] text-white text-sm focus:outline-none focus:border-violet-500/50"
                  >
                    <option value="">Select a bundle...</option>
                    {bundles.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </motion.div>

          {/* Members */}
          <motion.div variants={fadeUp}>
            <h2 className="text-lg font-semibold text-white/80 mb-4">Team Members</h2>
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              {team.members?.map((member) => (
                <div key={member.user_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-violet-700/30 flex items-center justify-center">
                      <span className="text-sm font-medium text-violet-300">
                        {member.name?.[0] || member.email[0]}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white/80">{member.name || member.email}</p>
                      <p className="text-xs text-white/40">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/30 capitalize">{member.role}</span>
                    {member.role !== "owner" && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="p-1.5 rounded-lg hover:bg-red-500/15 text-white/25 hover:text-red-400 transition-colors"
                      >
                        <User size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {/* Invite Member */}
              <div className="border-t border-white/[0.06] pt-4">
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="Invite by email..."
                    className="flex-1 px-3 py-2 rounded-lg border border-white/[0.08] bg-white/[0.02] text-white placeholder-white/30 text-sm focus:outline-none focus:border-violet-500/50"
                  />
                  <button
                    onClick={handleInvite}
                    disabled={!inviteEmail.trim() || inviting}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 disabled:opacity-50 transition-colors"
                  >
                    {inviting ? (
                      <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Envelope size={14} />
                    )}
                    Invite
                  </button>
                </div>
                {error && (
                  <p className="text-xs text-red-400 mt-2">{error}</p>
                )}
              </div>
            </div>
          </motion.div>

        </motion.div>
      </main>
    </div>
  );
}
