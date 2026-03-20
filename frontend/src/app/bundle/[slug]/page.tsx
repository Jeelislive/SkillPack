import { Metadata } from "next";
import BundlePageClient from "./BundlePageClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchBundle(slug: string) {
  try {
    const res = await fetch(`${API_URL}/api/bundles/${slug}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const bundle = await fetchBundle(slug);

  if (!bundle) {
    return { title: "Bundle Not Found" };
  }

  const name = bundle.name as string;
  const description = (bundle.description as string) ||
    `Install the ${name} skill bundle for Claude Code, Cursor, Copilot, and more. ${bundle.skill_count} curated skills in one command.`;
  const title = `${name} — AI Agent Skill Bundle`;
  const url = `https://skillpack.dev/bundle/${slug}`;

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      type: "website",
      siteName: "SkillPack",
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default async function BundlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const bundle = await fetchBundle(slug);

  // JSON-LD: SoftwareApplication + BreadcrumbList
  const jsonLd = bundle
    ? {
        "@context": "https://schema.org",
        "@graph": [
          {
            "@type": "BreadcrumbList",
            itemListElement: [
              { "@type": "ListItem", position: 1, name: "Home", item: "https://skillpack.dev" },
              { "@type": "ListItem", position: 2, name: "Explore", item: "https://skillpack.dev/explore" },
              { "@type": "ListItem", position: 3, name: bundle.name, item: `https://skillpack.dev/bundle/${slug}` },
            ],
          },
          {
            "@type": "SoftwareApplication",
            name: bundle.name,
            description: bundle.description,
            applicationCategory: "DeveloperApplication",
            operatingSystem: "Any",
            url: `https://skillpack.dev/bundle/${slug}`,
            offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
          },
        ],
      }
    : null;

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <BundlePageClient slug={slug} />
    </>
  );
}
