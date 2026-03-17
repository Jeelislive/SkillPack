# SkillPack - Full Product Plan

> Aggregate every AI agent skill on the internet. Bundle them by role. Install with one command.

---

## 1. The Problem

Every developer using AI agents (Claude Code, Cursor, Copilot, etc.) needs skills - small instruction files that teach the agent how to think about specific tasks. Right now:

- Skills are scattered across GitHub, skills.sh, cursor.directory, and dozens of other places
- Developers discover them randomly or by word of mouth
- Installing them means finding each one individually and running separate commands
- There is no concept of "get everything I need as a frontend developer in one shot"
- Quality is unknown - there's no scoring, no curation, no ranking

**Result:** Developers waste time hunting, install random low-quality skills, and never get a complete setup.

---

## 2. The Solution

SkillPack is a **skill aggregator + AI bundler**. It:

1. Crawls every source on the internet for AI agent skills (110,000+ indexed)
2. Stores the best ones in its own database (quality-filtered)
3. Bundles them by role and task using keyword matching + AI
4. Generates a **single install command** per platform per bundle
5. Works across Claude Code, Cursor, GitHub Copilot, Continue.dev, and more

**Core user flow:**
```
User types: "I build React frontends"
         ↓
SkillPack matches → Frontend Developer bundle
         ↓
Shows 30 best skills for frontend work
         ↓
User picks platform (Claude Code / Cursor / Copilot)
         ↓
Copies ONE command → installs all 30 skills instantly
```

---

## 3. What Makes This Different

| Feature | skills.sh | SkillPack |
|---------|-----------|-----------|
| Skills indexed | 88k | 110k+ (7 sources) |
| Install one skill | ✓ | ✓ |
| Install a bundle | ✗ | ✓ |
| Role-based discovery | ✗ | ✓ |
| Natural language matching | ✗ | ✓ |
| Multi-platform commands | Partial | ✓ (5 platforms) |
| Quality scoring | Install count only | Install count + content depth + stars |
| Live fetch for rare skills | ✗ | ✓ (tier 2) |
| Free | ✓ | ✓ (forever) |

---

## 4. Data Sources (7 Total)

| # | Source | Est. Volume | Method | Status |
|---|--------|------------|--------|--------|
| 1 | skills.sh | 88,000 | HTML scrape + GitHub raw fetch | Planned |
| 2 | GitHub Search (`filename:SKILL.md`) | ~20–50k | GitHub Search API | Planned |
| 3 | microsoft/skills repo | ~500 | Direct repo crawl | Planned |
| 4 | cursor.directory + awesome-cursorrules | ~500 | GitHub search `.cursorrules` | Planned |
| 5 | Continue.dev hub | ~200 | API + scrape | Planned |
| 6 | GitHub Copilot skills | ~500 | GitHub search + Copilot docs | Planned |
| 7 | MCP Registry (Model Context Protocol) | Growing | GitHub search + registry API | Planned |

**Total target: 110,000+ skills indexed**

### Tier System
- **Tier 1 (stored in DB):** Top ~20–25k skills by quality score - instant API response
- **Tier 2 (live fetch):** Remaining 80k+ - fetched on-demand from GitHub raw URL, cached in Redis 24hr

---

## 5. Tech Stack

### Backend
| Layer | Technology | Why |
|-------|-----------|-----|
| API Framework | FastAPI (Python) | Async, fast, great for AI pipelines |
| Database | PostgreSQL (Supabase free) | Relational, pg_trgm for text search |
| Cache | Redis (Upstash free) | Tier 2 skill caching, API response cache |
| Job Queue | Celery + Redis | Daily scheduled crawls |
| HTTP Client | httpx (async) | Fast concurrent fetching |
| HTML Parser | BeautifulSoup + lxml | Scraping skills.sh, cursor.directory |

### AI / Intelligence
| Task | Tool | Why |
|------|------|-----|
| Skill categorization (bulk) | Keyword heuristics | No rate limits, instant, processes all 110k |
| Bundle-to-query matching | Groq (llama-3.3-70b-versatile) | Single call per user search, free |
| AI fallback | NVIDIA NIM (free credits) | Backup when Groq fails |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Data Fetching | fetch + SWR |
| Icons | lucide-react |
| Deployment | Vercel (free) |

### Infrastructure (All Free)
| Service | Provider | Free Limit |
|---------|---------|-----------|
| Database | Supabase | 500MB |
| Backend API | Render.com | 750 hrs/mo |
| Frontend | Vercel | Unlimited |
| Redis | Upstash | 10k cmds/day |
| AI (primary) | Groq | ~30 req/min |
| AI (fallback) | NVIDIA NIM | Free credits |

---

## 6. Database Schema

```
sources          - 7 crawl sources (skills_sh, github, microsoft, cursor, continue, mcp...)
skills           - Tier 1: full content stored (20–25k high-quality skills)
skills_index     - Tier 2: metadata only, live-fetched on demand (80k+ skills)
bundles          - 17+ curated role/task bundles
bundle_commands  - Install commands per bundle per platform (5 platforms)
crawl_jobs       - Job history, stats, error logs
```

### Storage Budget (Supabase 500MB free)
```
Tier 1 skill content (20k × 5KB avg, TOAST compressed ~3x): ~35MB
Metadata + arrays (tags, categories, keywords):              ~40MB
Indexes (pg_trgm, GIN, btree):                              ~50MB
Bundles + commands:                                          ~5MB
─────────────────────────────────────────────────────────────────
Total estimate:                                             ~130MB  ✓ well under 500MB
```

---

## 7. Crawl Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  CRAWLERS (daily via Celery, or manual via run_crawl.py)    │
│                                                             │
│  skills_sh.py    → scrape leaderboard pages                 │
│                  → fetch SKILL.md from GitHub raw URL       │
│                                                             │
│  github_crawler.py → GitHub Search API (6 queries)         │
│                    → filename:SKILL.md                      │
│                    → filename:.cursorrules                  │
│                    → topic:agent-skills etc.                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  TAGGER (heuristic, instant, no rate limits)                │
│                                                             │
│  For each skill:                                            │
│  1. Read name + description + SKILL.md content              │
│  2. Keyword match → primary_category                        │
│  3. Keyword match → sub_categories, tags                    │
│  4. quality_score = f(content_length, depth)                │
│  5. popularity_score = f(install_count, github_stars)       │
│                                                             │
│  Result: every skill tagged in milliseconds                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  TIER SPLIT                                                 │
│                                                             │
│  quality_score >= 4 AND has content → Tier 1 (store in DB) │
│  quality_score < 4 OR no content   → Tier 2 (index only)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  BUNDLE GENERATOR                                           │
│                                                             │
│  For each of 17 bundles:                                    │
│  1. Query DB: skills matching category + keywords           │
│  2. Sort by: quality_score×0.6 + popularity_score×0.4      │
│  3. Take top 30                                             │
│  4. Generate install commands for 5 platforms               │
│  5. Store in bundles + bundle_commands tables               │
└─────────────────────────────────────────────────────────────┘
```

### Crawl Schedule
- **Daily at 2:00 AM UTC** - full crawl of all sources
- **Daily at 4:00 AM UTC** - bundle regeneration (after crawl)
- **Change detection** - content hash comparison, only re-process changed skills

---

## 8. Skill Quality Scoring

Each skill gets two scores (0–10):

### Quality Score (content depth)
| Condition | Score |
|-----------|-------|
| Content length > 3000 chars, structured with examples | 8–10 |
| Content 1000–3000 chars, good structure | 6–8 |
| Content 300–1000 chars, basic | 4–6 |
| Content < 300 chars, stub | 0–4 |

### Popularity Score (usage signals)
```
popularity = log10(install_count + 1) × 2 × 0.7
           + log10(github_stars + 1) × 2.5 × 0.3
```

### Final Bundle Rank
```
rank = quality_score × 0.6 + popularity_score × 0.4
```
Quality weighted higher than popularity - a deeply written skill beats a viral stub.

---

## 9. Bundles

### Role Bundles (12)
| Slug | Name | Category |
|------|------|----------|
| `frontend` | Frontend Developer | frontend |
| `backend` | Backend Developer | backend |
| `fullstack` | Full Stack Developer | fullstack |
| `devops` | DevOps Engineer | devops |
| `data-science` | Data Scientist | data-science |
| `ml-ai` | ML / AI Engineer | ml-ai |
| `security` | Security Engineer | security |
| `mobile` | Mobile Developer | mobile |
| `database` | Database Engineer | database |
| `testing` | QA / Testing Engineer | testing |
| `cloud` | Cloud Engineer | cloud |
| `api-design` | API Designer | api-design |

### Task Bundles (5)
| Slug | Name |
|------|------|
| `build-landing-page` | Build a Landing Page |
| `setup-cicd` | Set Up CI/CD Pipeline |
| `write-unit-tests` | Write Unit Tests |
| `design-rest-api` | Design a REST API |
| `setup-auth` | Implement Authentication |

### Future: Micro Bundles
Small, hyper-specific bundles for individual tasks:
- `react-hooks`, `css-animations`, `docker-compose`, `jwt-auth`, `postgres-queries` etc.

---

## 10. Install Command Generation

For each bundle, we pre-generate commands for 5 platforms:

### Claude Code
```bash
npx skills add vercel-labs/next-best-practices anthropic/prompt-engineering ...
```

### Cursor
```bash
#!/bin/bash
# Appends all skill content to .cursorrules
curl -s https://raw.githubusercontent.com/owner/repo/main/SKILL.md >> .cursorrules
...
```

### GitHub Copilot
```bash
#!/bin/bash
# Injects into .github/copilot-instructions.md
curl -s https://raw.githubusercontent.com/owner/repo/main/SKILL.md >> .github/copilot-instructions.md
...
```

### Continue.dev
```bash
#!/bin/bash
# Downloads skills to ~/.continue/skills/
curl -s https://raw.githubusercontent.com/owner/repo/main/SKILL.md > ~/.continue/skills/skill-name.md
```

### Universal (shell script)
```bash
#!/bin/bash
# Auto-detects or accepts --platform flag
PLATFORM="${1:-claude_code}"
case "$PLATFORM" in
  claude_code) npx skills add ... ;;
  cursor)      curl ... >> .cursorrules ;;
  ...
esac
```

---

## 11. API Endpoints

### Bundles
```
GET  /api/bundles                     - list all bundles
GET  /api/bundles/{slug}              - bundle detail + skills + commands
GET  /api/bundles/{slug}/install/{platform} - get install command (+ track count)
```

### Skills
```
GET  /api/skills                      - list tier-1 skills (filter by category, platform)
GET  /api/skills/categories           - category counts
GET  /api/skills/{owner}/{repo}       - individual skill detail
```

### Search
```
GET  /api/search?q=...                - full-text search across skills
GET  /api/search/match-bundle?q=...   - NL input → best bundle match (Groq)
```

### Live Fetch (Tier 2)
```
GET  /api/live/{owner}/{repo}         - fetch SKILL.md on-demand, cache 24hr
```

### Admin / Crawl
```
POST /api/crawl/trigger/full          - trigger full crawl
POST /api/crawl/trigger/skills-sh     - trigger skills.sh crawl only
POST /api/crawl/trigger/github        - trigger GitHub crawl only
POST /api/crawl/trigger/bundles       - regenerate bundles
GET  /api/crawl/stats                 - skill counts, source status
GET  /api/crawl/jobs                  - crawl job history
```

---

## 12. Frontend Pages

### `/` - Home
- Big NL input: "What kind of developer are you?"
- Rotating placeholder examples
- Role bundle cards grid (12 cards)
- Stats bar: skills indexed, bundles, platforms
- How it works (3 steps)

### `/bundle/[slug]` - Bundle Detail
- Bundle name, description, skill count, install count
- Platform selector tabs (Claude Code / Cursor / Copilot / Continue / Universal)
- Copy install command (big, prominent)
- Collapsible skills list (name, slug, tags, quality score, source link)
- Individual skill install command

### `/explore` - Browse
- Tab: Bundles | Skills
- Filter bundles by type (role / task / micro)
- Search skills by keyword
- Skills list with inline install command preview

### `/skills/[owner]/[repo]` - Skill Detail *(future)*
- Full SKILL.md rendered as markdown
- Quality score + popularity score
- Bundles that include this skill
- Install command
- GitHub repo link

### `/status` - Data Freshness *(future)*
- Last crawl time per source
- Total skills per source
- Crawl job history

---

## 13. Project Structure

```
skillpack/
├── backend/
│   ├── .env                        ← environment variables
│   ├── config.py                   ← settings (Pydantic)
│   ├── run_crawl.py                ← first-run / manual crawl script
│   ├── requirements.txt
│   │
│   ├── db/
│   │   ├── schema.sql              ← PostgreSQL schema
│   │   ├── models.py               ← SQLAlchemy ORM models
│   │   ├── database.py             ← async + sync engine, session factories
│   │   └── ingestion.py            ← upsert logic for skills + skill_index
│   │
│   ├── crawlers/
│   │   ├── skills_sh.py            ← skills.sh leaderboard scraper
│   │   └── github_crawler.py       ← GitHub Search API crawler
│   │
│   ├── pipeline/
│   │   ├── tagger.py               ← heuristic tagger + Groq AI tagger
│   │   ├── bundle_generator.py     ← builds + updates all 17 bundles
│   │   └── install_generator.py    ← generates install commands per platform
│   │
│   ├── api/
│   │   ├── main.py                 ← FastAPI app + CORS + router registration
│   │   └── routes/
│   │       ├── bundles.py
│   │       ├── skills.py
│   │       ├── search.py           ← text search + Groq bundle matching
│   │       ├── live.py             ← on-demand tier-2 skill fetch
│   │       └── crawl.py            ← admin crawl triggers + stats
│   │
│   └── workers/
│       ├── celery_app.py           ← Celery config + daily beat schedule
│       └── tasks.py                ← crawl + bundle regen tasks
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx            ← home page
    │   │   ├── bundle/[slug]/      ← bundle detail
    │   │   └── explore/            ← browse + search
    │   ├── components/
    │   │   ├── BundleCard.tsx
    │   │   ├── InstallCommand.tsx  ← copy button + mono display
    │   │   └── PlatformSelector.tsx
    │   └── lib/
    │       └── api.ts              ← typed API client
    └── .env.local
```

---

## 14. Build Phases

### Phase 1 - Data Foundation ✅ Done
- [x] PostgreSQL schema on Supabase (6 tables, indexes, sources seeded)
- [x] SQLAlchemy models
- [x] skills.sh scraper
- [x] GitHub Search API crawler
- [x] Heuristic skill tagger (instant, no rate limits)
- [x] DB ingestion (upsert, tier split, change detection)
- [x] Bundle generator (17 bundles × 5 platforms)
- [x] Install command generator (5 platform formats)
- [x] Celery daily schedule

### Phase 2 - API Layer ✅ Done
- [x] FastAPI app + CORS
- [x] Bundles routes
- [x] Skills routes
- [x] Search routes (text + NL bundle matching)
- [x] Live fetch route (tier-2 on-demand)
- [x] Admin/crawl routes

### Phase 3 - Frontend ✅ Done
- [x] Next.js 14 setup (TypeScript, Tailwind, App Router)
- [x] Home page (NL search + role cards + stats)
- [x] Bundle detail page (platform selector + install command + skills list)
- [x] Explore page (browse + search)
- [x] BundleCard, InstallCommand, PlatformSelector components
- [x] Typed API client

### Phase 4 - First Data (Next)
- [ ] Run `run_crawl.py` to populate DB with real skills
- [ ] Verify bundle generation works with real data
- [ ] Start FastAPI server locally
- [ ] Test full user flow end-to-end

### Phase 5 - Deploy
- [ ] Deploy frontend to Vercel
- [ ] Deploy FastAPI to Render.com
- [ ] Set up Upstash Redis
- [ ] Configure environment variables on both platforms
- [ ] Run production crawl
- [ ] Domain setup

### Phase 6 - More Sources
- [ ] cursor.directory scraper
- [ ] Continue.dev hub scraper
- [ ] MCP registry crawler
- [ ] microsoft/skills repo crawler

### Phase 7 - Polish
- [ ] Individual skill detail pages (`/skills/[owner]/[repo]`)
- [ ] Status/freshness page
- [ ] Analytics (Plausible, self-hosted free)
- [ ] SEO: bundle pages pre-rendered, meta tags, sitemap
- [ ] Share bundle URL feature

### Phase 8 - Growth
- [ ] Submit to GitHub Awesome lists
- [ ] Post on Hacker News, Reddit r/ClaudeAI, r/cursor
- [ ] Discord community
- [ ] Track installs per bundle for social proof
- [ ] "Trending skills this week" section on home

---

## 15. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Supabase async connection string |
| `SYNC_DATABASE_URL` | ✅ | Supabase sync connection string |
| `GROQ_API_KEY` | ✅ | Groq AI (bundle matching only) |
| `GITHUB_TOKEN` | ✅ | GitHub API (Search, raw content) |
| `NVIDIA_API_KEY` | Optional | NVIDIA NIM fallback |
| `GITHUB_TOKEN_2` | Optional | Second token for higher rate limits |
| `REDIS_URL` | Optional | Upstash Redis (tier-2 caching + Celery) |

**Frontend:**
| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` |

---

## 16. Constraints & Trade-offs

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| DB storage | Store top 20k (quality filtered) | Store all 110k | Supabase 500MB free limit |
| Tagging | Keyword heuristics | Full AI tagging | No rate limits, processes all skills in seconds |
| AI use | Only for bundle matching (1 call/search) | AI for everything | Free tier friendly |
| Search | pg_trgm full-text | Vector/semantic search | pgvector costs extra, trgm is sufficient for MVP |
| Hosting | 100% free stack | Paid infra | Zero cost until traction |

---

## 17. Future Ideas (Post-Launch)

- **Custom bundles** - let users create and share their own bundles
- **Skill submit** - developers can submit their own SKILL.md repos
- **Browser extension** - detect which agent platform you're on, suggest relevant skills
- **VS Code extension** - install bundles directly from the editor
- **Skill updates** - notify users when a skill in their bundle gets updated
- **Team bundles** - private bundles for dev teams (shared standards)
- **Skill quality AI review** - use AI to deeply evaluate skill quality monthly

---

## 18. Success Metrics

| Metric | Target (month 1) | Target (month 3) |
|--------|-----------------|-----------------|
| Skills indexed | 110k | 150k |
| Unique visitors | 500 | 5,000 |
| Bundle installs | 1,000 | 20,000 |
| GitHub stars | 50 | 500 |

---

*Last updated: March 2026*
