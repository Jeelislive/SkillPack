"use client";

import { useSession, signOut } from "next-auth/react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Lightning, SignOut, Package, Star } from "@phosphor-icons/react";
import Link from "next/link";
import Image from "next/image";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show:   { opacity: 1, y: 0 },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

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
      {/* Background */}
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 45% at 50% -5%, rgba(124,58,237,0.11) 0%, transparent 65%)",
        }}
      />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-700 flex items-center justify-center shadow-lg shadow-violet-950/50">
              <Lightning size={14} className="text-white" />
            </div>
            <span className="font-bold tracking-tight">SkillPack</span>
          </Link>

          <button
            onClick={() => signOut({ callbackUrl: "/" })}
            className="flex items-center gap-2 text-sm text-white/40 hover:text-white/80 transition-colors duration-200"
          >
            <SignOut size={15} />
            Sign out
          </button>
        </div>
      </nav>

      {/* Content */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-14 pb-24">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="space-y-10"
        >
          {/* Profile card */}
          <motion.div
            variants={fadeUp}
            className="rounded-3xl border border-white/[0.08] bg-white/[0.03] backdrop-blur p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6"
          >
            {user.image ? (
              <Image
                src={user.image}
                alt={user.name ?? "Avatar"}
                width={72}
                height={72}
                className="rounded-2xl ring-2 ring-violet-500/30 shrink-0"
              />
            ) : (
              <div className="w-[72px] h-[72px] rounded-2xl bg-violet-700/30 flex items-center justify-center shrink-0">
                <span className="text-2xl font-bold text-violet-300">
                  {user.name?.[0] ?? "?"}
                </span>
              </div>
            )}

            <div className="text-center sm:text-left">
              <h1 className="text-xl font-bold">{user.name}</h1>
              {user.email && (
                <p className="text-sm text-white/40 mt-0.5">{user.email}</p>
              )}
              <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-violet-300/80 border border-violet-500/20 rounded-full px-3 py-1 bg-violet-500/5">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                GitHub account connected
              </div>
            </div>
          </motion.div>

          {/* Coming soon sections */}
          <motion.div variants={fadeUp}>
            <h2 className="text-lg font-semibold mb-4 text-white/80">
              Your saved skills
            </h2>
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{
                  background: "rgba(124,58,237,0.10)",
                  border: "1px solid rgba(124,58,237,0.18)",
                }}
              >
                <Star size={20} className="text-violet-400" />
              </div>
              <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                Your saved skills coming soon. Browse the explore page to
                discover skills you love.
              </p>
              <Link
                href="/explore"
                className="text-xs text-violet-400/70 hover:text-violet-400 transition-colors border border-violet-500/20 rounded-lg px-4 py-2 bg-violet-500/5 hover:bg-violet-500/10"
              >
                Explore skills
              </Link>
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <h2 className="text-lg font-semibold mb-4 text-white/80">
              Your saved bundles
            </h2>
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 flex flex-col items-center text-center gap-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{
                  background: "rgba(59,130,246,0.10)",
                  border: "1px solid rgba(59,130,246,0.18)",
                }}
              >
                <Package size={20} className="text-blue-400" />
              </div>
              <p className="text-sm text-white/35 max-w-xs leading-relaxed">
                Your saved bundles coming soon. Find the perfect bundle for
                your developer role.
              </p>
              <Link
                href="/explore"
                className="text-xs text-blue-400/70 hover:text-blue-400 transition-colors border border-blue-500/20 rounded-lg px-4 py-2 bg-blue-500/5 hover:bg-blue-500/10"
              >
                Browse bundles
              </Link>
            </div>
          </motion.div>
        </motion.div>
      </main>
    </div>
  );
}
