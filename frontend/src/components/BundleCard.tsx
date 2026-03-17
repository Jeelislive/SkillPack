"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight, Star, Heart,
  Browser, Gear, Stack, Rocket, Brain, ShieldCheck,
  Database, Flask, Cloud, DeviceMobile, ChartBar, Package,
} from "@phosphor-icons/react";
import type { Bundle } from "@/lib/api";
import { useSession } from "next-auth/react";
import { useState } from "react";

type CatStyle = { Icon: React.ElementType; text: string; bg: string; border: string; glow: string };

const CAT: Record<string, CatStyle> = {
  frontend:       { Icon: Browser,      text: "#60a5fa", bg: "rgba(96,165,250,0.06)",  border: "rgba(96,165,250,0.16)",  glow: "0 12px 40px rgba(96,165,250,0.12)"  },
  backend:        { Icon: Gear,         text: "#4ade80", bg: "rgba(74,222,128,0.06)",  border: "rgba(74,222,128,0.16)",  glow: "0 12px 40px rgba(74,222,128,0.12)"  },
  fullstack:      { Icon: Stack,        text: "#c084fc", bg: "rgba(192,132,252,0.06)", border: "rgba(192,132,252,0.16)", glow: "0 12px 40px rgba(192,132,252,0.12)" },
  devops:         { Icon: Rocket,       text: "#fb923c", bg: "rgba(251,146,60,0.06)",  border: "rgba(251,146,60,0.16)",  glow: "0 12px 40px rgba(251,146,60,0.12)"  },
  "ml-ai":        { Icon: Brain,        text: "#f472b6", bg: "rgba(244,114,182,0.06)", border: "rgba(244,114,182,0.16)", glow: "0 12px 40px rgba(244,114,182,0.12)" },
  security:       { Icon: ShieldCheck,  text: "#f87171", bg: "rgba(248,113,113,0.06)", border: "rgba(248,113,113,0.16)", glow: "0 12px 40px rgba(248,113,113,0.12)" },
  database:       { Icon: Database,     text: "#22d3ee", bg: "rgba(34,211,238,0.06)",  border: "rgba(34,211,238,0.16)",  glow: "0 12px 40px rgba(34,211,238,0.12)"  },
  testing:        { Icon: Flask,        text: "#facc15", bg: "rgba(250,204,21,0.06)",  border: "rgba(250,204,21,0.16)",  glow: "0 12px 40px rgba(250,204,21,0.12)"  },
  cloud:          { Icon: Cloud,        text: "#38bdf8", bg: "rgba(56,189,248,0.06)",  border: "rgba(56,189,248,0.16)",  glow: "0 12px 40px rgba(56,189,248,0.12)"  },
  mobile:         { Icon: DeviceMobile, text: "#818cf8", bg: "rgba(129,140,248,0.06)", border: "rgba(129,140,248,0.16)", glow: "0 12px 40px rgba(129,140,248,0.12)" },
  "data-science": { Icon: ChartBar,     text: "#a3e635", bg: "rgba(163,230,53,0.06)",  border: "rgba(163,230,53,0.16)",  glow: "0 12px 40px rgba(163,230,53,0.12)"  },
};
const DEFAULT_CAT: CatStyle = { Icon: Package, text: "rgba(255,255,255,0.45)", bg: "rgba(255,255,255,0.03)", border: "rgba(255,255,255,0.09)", glow: "0 8px 24px rgba(0,0,0,0.3)" };

export default function BundleCard({ 
  bundle, 
  isSaved = false, 
  onSave, 
  isLoading = false 
}: { 
  bundle: Bundle; 
  isSaved?: boolean; 
  onSave?: () => void; 
  isLoading?: boolean;
}) {
  const { data: session } = useSession();
  const s = CAT[bundle.category] ?? DEFAULT_CAT;

  return (
    <Link href={`/bundle/${bundle.slug}`} className="block h-full">
      <motion.div
        whileHover={{ y: -4, boxShadow: s.glow }}
        transition={{ duration: 0.22, ease: "easeOut" }}
        className="relative rounded-2xl p-5 h-full flex flex-col cursor-pointer"
        style={{ background: s.bg, border: `1px solid ${s.border}` }}
      >
        {bundle.is_featured && (
          <Star
            size={11}
            className="absolute top-4 right-4"
            style={{ color: s.text, fill: "currentColor" }}
          />
        )}

        {session && onSave && (
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onSave();
            }}
            disabled={isLoading}
            className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-white/[0.1] transition-colors disabled:opacity-50"
          >
            <Heart 
              size={14} 
              weight={isSaved ? "fill" : "regular"}
              className={isSaved ? "text-red-400" : "text-white/40"}
            />
          </button>
        )}

        <div className="flex items-start gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: `${s.text}14`, border: `1px solid ${s.text}22` }}
          >
            <s.Icon size={18} weight="duotone" style={{ color: s.text }} />
          </div>
          <div className="min-w-0 pt-0.5">
            <h3 className="font-semibold text-sm text-white leading-snug">{bundle.name}</h3>
            <span className="font-mono text-[11px]" style={{ color: s.text }}>
              {bundle.type}
            </span>
          </div>
        </div>

        <p className="text-xs text-white/40 leading-relaxed flex-1 mb-4 line-clamp-2">
          {bundle.description || `Curated ${bundle.name} skills for AI agents.`}
        </p>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 font-mono text-[11px] text-white/25">
            <span>{bundle.skill_count} skills</span>
            {bundle.install_count > 0 && (
              <span>{bundle.install_count.toLocaleString()} installs</span>
            )}
          </div>
          <ArrowRight size={13} style={{ color: s.text, opacity: 0.5 }} />
        </div>
      </motion.div>
    </Link>
  );
}
