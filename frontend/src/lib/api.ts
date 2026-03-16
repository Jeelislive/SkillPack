const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Simple in-memory cache for client-side fetches (pages are "use client" + useEffect,
// so Next.js fetch revalidate does nothing here)
const _mem = new Map<string, { data: unknown; exp: number }>();
const _TTL = 2 * 60 * 1000; // 2 minutes

function _cached<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const hit = _mem.get(key);
  if (hit && Date.now() < hit.exp) return Promise.resolve(hit.data as T);
  return fetcher().then((data) => {
    _mem.set(key, { data, exp: Date.now() + _TTL });
    return data;
  });
}

export interface Bundle {
  id: number;
  slug: string;
  name: string;
  description: string;
  type: "role" | "task" | "micro";
  category: string;
  skill_count: number;
  install_count: number;
  is_featured: boolean;
  skills?: Skill[];
  commands?: Record<string, string>;
}

export interface Skill {
  id: number;
  slug: string;
  name: string;
  description: string;
  primary_category: string;
  sub_categories: string[];
  tags: string[];
  platforms: string[];
  install_command: string;
  quality_score: number;
  popularity_score: number;
  install_count: number;
  github_stars: number;
  role_keywords: string[];
  task_keywords: string[];
  source_url: string;
  raw_url?: string;
  raw_content?: string;
}

export interface SkillsPage {
  items: Skill[];
  total: number;
  offset: number;
  limit: number;
}

export interface SearchResult {
  query: string;
  results: Skill[];
}

export interface BundleMatch {
  query: string;
  matched_bundle: string;
  bundle_name: string;
  url: string;
}

export interface Stats {
  tier1_skills: number;
  tier2_skills: number;
  total_skills: number;
  sources: { name: string; display_name: string; total_skills: number; last_crawled_at: string }[];
}

async function get<T>(path: string, cache = true): Promise<T> {
  const fetcher = async () => {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json() as Promise<T>;
  };
  return cache ? _cached<T>(path, fetcher) : fetcher();
}

export const api = {
  bundles: {
    list: (params?: { type?: string; category?: string }) => {
      const q = new URLSearchParams(params as Record<string, string>).toString();
      return get<Bundle[]>(`/api/bundles${q ? `?${q}` : ""}`);
    },
    get: (slug: string) => get<Bundle>(`/api/bundles/${slug}`),
    installCommand: (slug: string, platform: string) =>
      get<{ platform: string; command: string; bundle: string }>(
        `/api/bundles/${slug}/install/${platform}`, false  // no cache — increments install count
      ),
  },
  skills: {
    list: (params?: { category?: string; platform?: string; limit?: number; offset?: number }) => {
      const q = new URLSearchParams(params as Record<string, string>).toString();
      return get<SkillsPage>(`/api/skills${q ? `?${q}` : ""}`);
    },
    categories: () => get<{ category: string; count: number }[]>("/api/skills/categories"),
    get: (slug: string) => get<Skill>(`/api/skills/${slug}`),
  },
  search: {
    skills: (q: string, params?: { category?: string; platform?: string }) => {
      const p = new URLSearchParams({ q, ...(params as Record<string, string>) }).toString();
      return get<SearchResult>(`/api/search?${p}`);
    },
    matchBundle: (q: string) =>
      get<BundleMatch>(`/api/search/match-bundle?q=${encodeURIComponent(q)}`),
  },
  live: {
    fetchSkill: (owner: string, repo: string) =>
      get<Skill>(`/api/live/${owner}/${repo}`),
  },
  stats: () => get<Stats>("/api/crawl/stats"),
};
