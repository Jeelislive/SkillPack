import type { Session } from "next-auth";

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
  type: "role" | "task" | "micro" | "custom";
  category: string;
  skill_count: number;
  install_count: number;
  is_featured: boolean;
  is_public?: boolean;
  owner_user_id?: string;
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

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  tier: "free" | "pro";
}

export interface SavesResponse {
  skills: Skill[];
  bundles: Bundle[];
  saved_skill_ids: number[];
  saved_bundle_ids: number[];
}

export interface Team {
  id: number;
  slug: string;
  name: string;
  owner_user_id: string;
  canonical_bundle_id: number | null;
  is_active: boolean;
  created_at: string;
  members?: TeamMember[];
}

export interface TeamMember {
  user_id: string;
  role: string;
  email: string;
  name: string | null;
  joined_at: string;
}

export interface RatingAggregate {
  avg: number;
  count: number;
  your_rating?: number;
}

// ── base fetch helpers ────────────────────────────────────────────────────────

async function get<T>(path: string, cache = true): Promise<T> {
  const fetcher = async () => {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json() as Promise<T>;
  };
  return cache ? _cached<T>(path, fetcher) : fetcher();
}

// ── authed helpers ────────────────────────────────────────────────────────────

function _authHeaders(session: Session | null): Record<string, string> {
  if (!session?.user) return {};
  return {
    "X-User-Id":    session.user.id    ?? "",
    "X-User-Email": session.user.email ?? "",
    "X-User-Name":  session.user.name  ?? "",
    "X-User-Image": session.user.image ?? "",
  };
}

async function authedGet<T>(path: string, session: Session | null): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: _authHeaders(session) });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

async function authedPost<T>(path: string, body: unknown, session: Session | null): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ..._authHeaders(session) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

async function authedPut<T>(path: string, body: unknown, session: Session | null): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ..._authHeaders(session) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

async function authedDelete<T>(path: string, session: Session | null): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: _authHeaders(session),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

// ── api object ────────────────────────────────────────────────────────────────

export const api = {
  bundles: {
    list: (params?: { type?: string; category?: string }) => {
      const q = new URLSearchParams(params as Record<string, string>).toString();
      return get<Bundle[]>(`/api/bundles${q ? `?${q}` : ""}`);
    },
    get: (slug: string) => get<Bundle>(`/api/bundles/${slug}`),
    installCommand: (slug: string, platform: string, session?: Session | null) => {
      const headers = session ? _authHeaders(session) : {};
      return fetch(`${API_BASE}/api/bundles/${slug}/install/${platform}`, { headers })
        .then((r) => { if (!r.ok) throw new Error(`API error: ${r.status}`); return r.json(); }) as Promise<{ platform: string; command: string; bundle: string }>;
    },
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

  user: {
    sync:   (session: Session | null) => authedPost<UserProfile>("/api/user/sync", {}, session),
    me:     (session: Session | null) => authedGet<UserProfile>("/api/user/me", session),
    bundles: {
      list:   (session: Session | null) => authedGet<Bundle[]>("/api/user/bundles", session),
      get:    (slug: string, session: Session | null) => authedGet<Bundle>(`/api/user/bundles/${slug}`, session),
      create: (body: { name: string; description?: string; skill_ids?: number[]; is_public?: boolean }, session: Session | null) =>
        authedPost<Bundle>("/api/user/bundles", body, session),
      update: (slug: string, body: Partial<{ name: string; description: string; skill_ids: number[]; is_public: boolean }>, session: Session | null) =>
        authedPut<Bundle>(`/api/user/bundles/${slug}`, body, session),
      delete: (slug: string, session: Session | null) =>
        authedDelete<{ ok: boolean }>(`/api/user/bundles/${slug}`, session),
    },
    saves: {
      list:         (session: Session | null) => authedGet<SavesResponse>("/api/user/saves", session),
      saveSkill:    (id: number, session: Session | null) => authedPost<{ ok: boolean; saved: boolean }>(`/api/user/saves/skill/${id}`, {}, session),
      unsaveSkill:  (id: number, session: Session | null) => authedDelete<{ ok: boolean; saved: boolean }>(`/api/user/saves/skill/${id}`, session),
      saveBundle:   (id: number, session: Session | null) => authedPost<{ ok: boolean; saved: boolean }>(`/api/user/saves/bundle/${id}`, {}, session),
      unsaveBundle: (id: number, session: Session | null) => authedDelete<{ ok: boolean; saved: boolean }>(`/api/user/saves/bundle/${id}`, session),
    },
  },

  teams: {
    list:             (session: Session | null) => authedGet<Team[]>("/api/teams", session),
    get:              (slug: string, session: Session | null) => authedGet<Team>(`/api/teams/${slug}`, session),
    create:           (body: { name: string; slug?: string }, session: Session | null) => authedPost<Team>("/api/teams", body, session),
    setCanonical:     (slug: string, bundle_id: number, session: Session | null) => authedPut<{ ok: boolean }>(`/api/teams/${slug}/canonical-bundle`, { bundle_id }, session),
    inviteMember:     (slug: string, email: string, session: Session | null) => authedPost<{ ok: boolean }>(`/api/teams/${slug}/members`, { email }, session),
    removeMember:     (slug: string, uid: string, session: Session | null) => authedDelete<{ ok: boolean }>(`/api/teams/${slug}/members/${uid}`, session),
    installLog:       (slug: string, session: Session | null) => authedGet<object[]>(`/api/teams/${slug}/install-log`, session),
    installCommand:   (slug: string) => get<{ command: string; team: string }>(`/api/teams/${slug}/install`),
  },

  ratings: {
    get:    (slug: string) => get<RatingAggregate>(`/api/skills/${slug}/ratings`, false),
    submit: (slug: string, rating: number, session: Session | null) =>
      authedPost<RatingAggregate>(`/api/skills/${slug}/rate`, { rating }, session),
  },
};
