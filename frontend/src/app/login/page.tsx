"use client";

import { signIn } from "next-auth/react";
import { motion } from "framer-motion";
import { Lightning, GoogleLogo, ArrowLeft } from "@phosphor-icons/react";
import Link from "next/link";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0 },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#060606] text-white flex flex-col overflow-x-hidden">
      {/* Background */}
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -5%, rgba(124,58,237,0.15) 0%, transparent 65%)",
        }}
      />

      {/* Back link */}
      <div className="relative z-10 p-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-white/35 hover:text-white/70 transition-colors duration-200"
        >
          <ArrowLeft size={14} />
          Back to home
        </Link>
      </div>

      {/* Centered card */}
      <div className="relative z-10 flex flex-1 items-center justify-center px-6 pb-20">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="w-full max-w-md"
        >
          {/* Card */}
          <motion.div
            variants={fadeUp}
            className="rounded-3xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl p-10 shadow-2xl shadow-black/60"
          >
            {/* Logo */}
            <motion.div variants={fadeUp} className="flex justify-center mb-8">
              <div className="w-14 h-14 rounded-2xl bg-violet-700 flex items-center justify-center shadow-lg shadow-violet-950/60">
                <Lightning size={24} weight="fill" className="text-white" />
              </div>
            </motion.div>

            {/* Title */}
            <motion.div variants={fadeUp} className="text-center mb-8">
              <h1 className="text-2xl font-bold tracking-tight mb-2">
                Welcome to SkillPack
              </h1>
              <p className="text-sm text-white/40 leading-relaxed">
                Sign in to save your favorite skills and bundles
              </p>
            </motion.div>

            {/* Google sign-in button */}
            <motion.div variants={fadeUp}>
              <motion.button
                onClick={() => signIn("google")}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className="w-full flex items-center justify-center gap-3 px-6 py-3.5 rounded-xl border border-violet-500/30 bg-white/[0.04] hover:bg-white/[0.08] hover:border-violet-500/50 transition-all duration-200 text-sm font-semibold shadow-lg shadow-black/30 group"
              >
                <GoogleLogo
                  size={20}
                  weight="fill"
                  className="text-white/80 group-hover:text-white transition-colors"
                />
                <span>Sign in with Google</span>
              </motion.button>
            </motion.div>

            {/* Divider */}
            <motion.div
              variants={fadeUp}
              className="my-7 flex items-center gap-3"
            >
              <div className="flex-1 h-px bg-white/[0.06]" />
              <span className="text-xs text-white/20 font-mono">or</span>
              <div className="flex-1 h-px bg-white/[0.06]" />
            </motion.div>

            {/* Free forever note */}
            <motion.p
              variants={fadeUp}
              className="text-center text-xs text-white/25 font-mono"
            >
              Free forever · No credit card required
            </motion.p>
          </motion.div>

          {/* Footer link */}
          <motion.p
            variants={fadeUp}
            className="text-center text-xs text-white/20 mt-6"
          >
            By signing in you agree to our{" "}
            <span className="text-violet-400/60 hover:text-violet-400 cursor-pointer transition-colors">
              Terms of Service
            </span>
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
