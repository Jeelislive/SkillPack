import { MetadataRoute } from "next";

const BASE_URL = "https://skillpack.dev";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface BundleSummary {
  slug: string;
  updated_at?: string;
}

interface SkillSummary {
  slug: string;
  updated_at?: string;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${BASE_URL}/explore`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
  ];

  let bundlePages: MetadataRoute.Sitemap = [];
  let skillPages: MetadataRoute.Sitemap = [];

  try {
    const [bundlesRes, skillsRes] = await Promise.all([
      fetch(`${API_URL}/api/bundles`, { next: { revalidate: 3600 } }),
      fetch(`${API_URL}/api/skills?limit=500`, { next: { revalidate: 3600 } }),
    ]);

    if (bundlesRes.ok) {
      const bundles: BundleSummary[] = await bundlesRes.json();
      bundlePages = bundles.map((b) => ({
        url: `${BASE_URL}/bundle/${b.slug}`,
        lastModified: b.updated_at ? new Date(b.updated_at) : new Date(),
        changeFrequency: "weekly",
        priority: 0.8,
      }));
    }

    if (skillsRes.ok) {
      const data = await skillsRes.json();
      const skills: SkillSummary[] = data.skills ?? data ?? [];
      skillPages = skills.slice(0, 200).map((s) => ({
        url: `${BASE_URL}/skills/${s.slug}`,
        lastModified: s.updated_at ? new Date(s.updated_at) : new Date(),
        changeFrequency: "monthly",
        priority: 0.6,
      }));
    }
  } catch {
    // Return static pages if API unavailable
  }

  return [...staticPages, ...bundlePages, ...skillPages];
}
