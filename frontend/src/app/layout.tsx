import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import AuthSessionProvider from "@/components/SessionProvider";
import UserSync from "@/components/UserSync";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SkillPack",
  description:
    "Discover and install curated AI agent skill bundles for Claude Code, Cursor, Copilot, and more. 110,000+ skills indexed, one install command.",
  openGraph: {
    title: "SkillPack — Curated AI Agent Skill Bundles",
    description: "One command for every skill your AI agent needs.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${plusJakarta.variable} antialiased`}
      >
        <AuthSessionProvider>
          <UserSync />
          {children}
        </AuthSessionProvider>
      </body>
    </html>
  );
}
