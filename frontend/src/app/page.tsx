"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, useInView } from "framer-motion";
import { MagnifyingGlass, ArrowRight, Lightning, Terminal } from "@phosphor-icons/react";
import Link from "next/link";
import BundleCard from "@/components/BundleCard";
import Navbar from "@/components/Navbar";
import { api, type Bundle } from "@/lib/api";

const PLATFORMS = [
  { label: "Claude Code", color: "#f97316" },
  { label: "Cursor",      color: "#6366f1" },
  { label: "Copilot",     color: "#22c55e" },
  { label: "Continue",    color: "#06b6d4" },
  { label: "Universal",   color: "#a855f7" },
];

const ROLE_EXAMPLES = [
  "frontend developer with React",
  "backend engineer with Node.js",
  "devops with Kubernetes",
  "ML engineer fine-tuning LLMs",
  "full stack developer",
  "security engineer",
];

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  show:   { opacity: 1, y: 0 },
};

function useCounter(end: number) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const duration = 1600;
    const start = performance.now();
    const frame = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - (1 - t) ** 3;
      setCount(Math.round(ease * end));
      if (t < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }, [inView, end]);

  return { ref, count };
}

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [phIdx, setPhIdx] = useState(0);

  const [bundleCount, setBundleCount] = useState(0);

  const { ref: s1ref, count: s1 } = useCounter(110000);
  const { ref: s2ref, count: s2 } = useCounter(bundleCount);
  const { ref: s3ref, count: s3 } = useCounter(5);

  useEffect(() => {
    api.bundles.list().then((b) => { setBundles(b); setBundleCount(b.length); }).catch(() => {});
    const t = setInterval(() => setPhIdx((i) => (i + 1) % ROLE_EXAMPLES.length), 3000);
    return () => clearInterval(t);
  }, []);

  const handleMagnifyingGlass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const m = await api.search.matchBundle(query);
      router.push(`/bundle/${m.matched_bundle}`);
    } catch {
      router.push(`/explore?q=${encodeURIComponent(query)}`);
    } finally {
      setLoading(false);
    }
  };

  const featured = bundles.filter((b) => b.type === "role").slice(0, 6);

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden">
      {/* Background */}
      <div className="fixed inset-0 dot-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 90% 55% at 50% -5%, rgba(124,58,237,0.13) 0%, transparent 65%)" }}
      />

      <Navbar />

      {/* Hero */}
      <section className="relative max-w-5xl mx-auto px-6 pt-28 pb-20 text-center">
        <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-8">

          <motion.div variants={fadeUp} className="flex justify-center">
            <div className="inline-flex items-center gap-2 text-xs font-medium text-violet-300/80 border border-violet-500/20 rounded-full px-4 py-1.5 bg-violet-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
              1,500+ skills indexed from 7 sources
            </div>
          </motion.div>

          <motion.h1 variants={fadeUp} className="text-6xl md:text-7xl font-bold tracking-tight leading-[1.06]">
            One command for
            <br />
            <span className="text-violet-400">every skill</span>{" "}
            you need
          </motion.h1>

          <motion.p variants={fadeUp} className="text-lg md:text-xl text-white/42 max-w-2xl mx-auto leading-relaxed">
            Describe your role. Get a curated bundle of AI agent skills — for Claude Code,
            Cursor, Copilot, or any platform. One install command.
          </motion.p>

          {/* MagnifyingGlass */}
          <motion.div variants={fadeUp} className="max-w-2xl mx-auto">
            <form onSubmit={handleMagnifyingGlass}>
              <div className="relative group">
                <div className="relative flex items-center rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur hover:border-white/20 hover:bg-white/[0.06] focus-within:border-violet-500/50 focus-within:bg-white/[0.05] focus-within:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] transition-all duration-200">
                  <MagnifyingGlass size={17} className="absolute left-5 text-white/25 shrink-0" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={ROLE_EXAMPLES[phIdx]}
                    className="w-full bg-transparent pl-12 pr-36 py-4 text-base outline-none placeholder:text-white/20 transition-all"
                  />
                  <motion.button
                    type="submit"
                    disabled={loading || !query.trim()}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    className="absolute right-2 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm font-semibold shadow-lg shadow-violet-950/40"
                  >
                    {loading ? (
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>Get Bundle <ArrowRight size={14} /></>
                    )}
                  </motion.button>
                </div>
              </div>
            </form>
            <p className="font-mono text-xs text-white/20 mt-3">
              try: &quot;frontend developer&quot; · &quot;devops with AWS&quot; · &quot;ML engineer&quot;
            </p>
          </motion.div>

          {/* Platform pills */}
          <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-2">
            {PLATFORMS.map((p) => (
              <div
                key={p.label}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
                style={{ border: `1px solid ${p.color}22`, background: `${p.color}08`, color: p.color }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: p.color }} />
                {p.label}
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="border-y border-white/[0.06] bg-white/[0.012] py-9">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-3 gap-8 text-center">
          <div ref={s1ref}>
            <div className="text-3xl font-bold font-mono">
              {s1 >= 1000 ? `${Math.floor(s1 / 1000)}K+` : s1}
            </div>
            <div className="text-[11px] uppercase tracking-widest text-white/30 mt-1.5">Skills Indexed</div>
          </div>
          <div ref={s2ref}>
            <div className="text-3xl font-bold font-mono">{s2}</div>
            <div className="text-[11px] uppercase tracking-widest text-white/30 mt-1.5">Curated Bundles</div>
          </div>
          <div ref={s3ref}>
            <div className="text-3xl font-bold font-mono">{s3}</div>
            <div className="text-[11px] uppercase tracking-widest text-white/30 mt-1.5">AI Platforms</div>
          </div>
        </div>
      </section>

      {/* Featured bundles */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="text-2xl font-bold">Role Bundles</h2>
            <p className="text-sm text-white/35 mt-1">Curated skill sets for every developer archetype</p>
          </div>
          <Link href="/explore" className="flex items-center gap-1.5 text-sm text-white/35 hover:text-white transition-colors">
            View all <ArrowRight size={13} />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(featured.length > 0 ? featured : Array(6).fill(null)).map((bundle, i) => (
            <motion.div
              key={bundle?.slug ?? i}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.07 }}
            >
              {bundle ? (
                <BundleCard bundle={bundle} />
              ) : (
                <div className="h-36 rounded-2xl border border-white/10 bg-white/[0.04] animate-pulse" />
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-white/[0.06] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold mb-3">How it works</h2>
            <p className="text-white/38">From description to installed skills in seconds</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {[
              { step: "01", icon: "💬", title: "Describe your role",   color: "#a855f7", desc: "Tell us what you build. Natural language — no config files, no YAML." },
              { step: "02", icon: "⚡", title: "Get your bundle",      color: "#3b82f6", desc: "We match the best skills from 110k+ indexed across GitHub and 6 other sources." },
              { step: "03", icon: "✓",  title: "One install command",  color: "#22c55e", desc: "Copy a single command. All skills installed into Claude Code, Cursor, Copilot, or any agent." },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.14 }}
                className="text-center"
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-5"
                  style={{ background: `${item.color}12`, border: `1px solid ${item.color}22` }}
                >
                  {item.icon}
                </div>
                <div className="font-mono text-xs text-white/20 mb-2">{item.step}</div>
                <h3 className="font-semibold text-base mb-2">{item.title}</h3>
                <p className="text-sm text-white/38 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mx-auto text-center rounded-3xl border border-white/8 bg-white/[0.03] p-16"
        >
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-6"
            style={{ background: "rgba(124,58,237,0.14)", border: "1px solid rgba(124,58,237,0.22)" }}
          >
            <Terminal size={22} className="text-violet-400" />
          </div>
          <h2 className="text-3xl font-bold mb-4">Ready to upgrade your AI agent?</h2>
          <p className="text-white/42 mb-9 text-lg">Browse 1,500+ skills and {bundleCount || "50+"} curated bundles. Free forever.</p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/explore">
              <motion.div
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="px-8 py-3.5 rounded-xl bg-violet-600 hover:bg-violet-500 transition-colors text-sm font-semibold shadow-lg shadow-violet-950/40 cursor-pointer"
              >
                Explore Skills
              </motion.div>
            </Link>
            <Link
              href="/explore"
              className="px-8 py-3.5 rounded-xl border border-white/10 text-sm font-medium text-white/55 hover:text-white hover:border-white/20 transition-all"
            >
              Browse Bundles
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-white/22">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-violet-600/25 flex items-center justify-center">
              <Lightning size={10} className="text-violet-400" />
            </div>
            <span className="font-medium text-white/38">SkillPack</span>
            <span>— Free forever</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/explore" className="hover:text-white/45 transition-colors">Explore</Link>
            <Link href="https://github.com" className="hover:text-white/45 transition-colors">GitHub</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
