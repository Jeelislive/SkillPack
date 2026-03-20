"use client";

import Link from "next/link";
import { GithubLogo, GoogleLogo } from "@phosphor-icons/react";
import { useSession, signIn, signOut } from "next-auth/react";
import Image from "next/image";
import Logo from "./Logo";

export default function Navbar() {
  const { data: session, status } = useSession({ required: false });

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-xl bg-[#060606]/75">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <Logo />
          <span className="font-bold tracking-tight">SkillPack</span>
        </Link>

        {/* Center nav links */}
        <div className="hidden md:flex items-center gap-8 text-sm text-white/40">
          <Link href="/explore" className="hover:text-white transition-colors duration-200">
            Explore
          </Link>
          <a
            href="https://github.com/Jeelislive/SkillPack"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition-colors duration-200"
          >
            <GithubLogo size={18} />
            <span className="hidden lg:inline">GitHub</span>
          </a>
        </div>

        {/* Auth section */}
        <div className="flex items-center gap-3">
          {status === "loading" ? (
            <span className="w-5 h-5 border-2 border-white/15 border-t-violet-500 rounded-full animate-spin" />
          ) : session?.user ? (
            <div className="flex items-center gap-3">
              {session.user.image && (
                <Image
                  src={session.user.image}
                  alt={session.user.name ?? "User avatar"}
                  width={28}
                  height={28}
                  className="w-7 h-7 rounded-full border border-white/10 object-cover"
                />
              )}
              <span className="text-sm text-white/60 hidden sm:block">{session.user.name}</span>
              <button
                onClick={() => signOut()}
                className="text-xs text-white/30 hover:text-white/60 transition-colors duration-200"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={() => signIn("google", { callbackUrl: "/" })}
              className="px-4 py-2 rounded-lg border border-violet-500/20 bg-violet-500/8 text-violet-300 hover:bg-violet-500/14 transition-all duration-200 text-sm flex items-center gap-2"
            >
              <GoogleLogo size={15} />
              Sign in with Google
            </button>
          )}
        </div>

      </div>
    </nav>
  );
}
