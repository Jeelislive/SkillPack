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
  title: {
    default: "SkillPack — Curated AI Agent Skill Bundles",
    template: "%s | SkillPack"
  },
  description:
    "Discover and install curated AI agent skill bundles for Claude Code, Cursor, Copilot, and more. 110,000+ skills indexed, one install command. Boost your AI agent's capabilities with role-specific skill sets.",
  keywords: [
    "AI skills",
    "Claude Code skills",
    "Cursor skills", 
    "Copilot skills",
    "AI agent bundles",
    "developer skills",
    "programming skills",
    "AI automation",
    "skill packs",
    "Claude extensions"
  ],
  authors: [{ name: "SkillPack Team" }],
  creator: "SkillPack",
  publisher: "SkillPack",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    title: "SkillPack — Curated AI Agent Skill Bundles",
    description: "One command for every skill your AI agent needs. 110,000+ skills indexed across 7 sources.",
    type: "website",
    url: "https://skillpack.dev",
    siteName: "SkillPack",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "SkillPack - AI Agent Skill Bundles",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SkillPack — Curated AI Agent Skill Bundles",
    description: "One command for every skill your AI agent needs. 110,000+ skills indexed.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "https://skillpack.dev",
    languages: {
      'en': 'https://skillpack.dev',
    },
  },
  other: {
    'theme-color': '#7c3aed',
    'msapplication-TileColor': '#7c3aed',
  },
};

const websiteJsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://skillpack.dev/#website",
      url: "https://skillpack.dev",
      name: "SkillPack",
      description: "Curated AI agent skill bundles for Claude Code, Cursor, Copilot, and more.",
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: "https://skillpack.dev/explore?q={search_term_string}",
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "Organization",
      "@id": "https://skillpack.dev/#organization",
      name: "SkillPack",
      url: "https://skillpack.dev",
      logo: {
        "@type": "ImageObject",
        url: "https://skillpack.dev/logo.svg",
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
      </head>
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
