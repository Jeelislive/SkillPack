import { Metadata } from "next";
import SkillDetailClient from "./SkillDetailClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchSkill(slug: string) {
  try {
    const res = await fetch(`${API_URL}/api/skills/${slug}`, {
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
  params: Promise<{ slug: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const slugStr = slug.join("/");
  const skill = await fetchSkill(slugStr);

  if (!skill) {
    return { title: "Skill Not Found" };
  }

  const name = skill.name as string;
  const category = skill.primary_category as string;
  const description =
    (skill.description as string) ||
    `Install the ${name} skill for Claude Code, Cursor, and Copilot. ${category} skill with quality score ${skill.quality_score?.toFixed(1)}/10.`;
  const title = `${name} — ${category} AI Skill`;
  const url = `https://skillpack.dev/skills/${slugStr}`;

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

export default async function SkillDetailPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const slugStr = slug.join("/");
  const skill = await fetchSkill(slugStr);

  const jsonLd = skill
    ? {
        "@context": "https://schema.org",
        "@graph": [
          {
            "@type": "BreadcrumbList",
            itemListElement: [
              { "@type": "ListItem", position: 1, name: "Home", item: "https://skillpack.dev" },
              { "@type": "ListItem", position: 2, name: "Explore", item: "https://skillpack.dev/explore" },
              { "@type": "ListItem", position: 3, name: skill.name, item: `https://skillpack.dev/skills/${slugStr}` },
            ],
          },
          {
            "@type": "SoftwareApplication",
            name: skill.name,
            description: skill.description,
            applicationCategory: "DeveloperApplication",
            operatingSystem: "Any",
            url: `https://skillpack.dev/skills/${slugStr}`,
            aggregateRating: skill.quality_score > 0
              ? {
                  "@type": "AggregateRating",
                  ratingValue: skill.quality_score.toFixed(1),
                  bestRating: "10",
                  worstRating: "0",
                  ratingCount: skill.install_count || 1,
                }
              : undefined,
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
      <SkillDetailClient slug={slugStr} />
    </>
  );
}
