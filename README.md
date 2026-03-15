<div align="center">

<img src="https://img.shields.io/badge/SkillPack-violet?style=for-the-badge&logo=lightning&logoColor=white" alt="SkillPack" height="40" />

# SkillPack

**Curated AI agent skill bundles. One install command.**

Describe your role → get a hand-picked bundle of 30 skills → install them all in one command across any AI coding platform.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js_16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-DD0031?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Python](https://img.shields.io/badge/Python_3.11+-3670A0?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

[Live Demo](#) · [API Docs](http://localhost:8000/docs) · [Report Bug](https://github.com/Jeelislive/SkillPack/issues)

</div>

---

## What is SkillPack?

SkillPack crawls **110,000+ AI agent skills** from [skills.sh](https://skills.sh) and GitHub, scores them with an LLM, and packages the best ones into **role-based bundles** — each with a single install command tailored to your platform.

| You type | You get |
|---|---|
| *"frontend developer with React"* | 30 skills: React best practices, Next.js, UI/UX, accessibility, performance, testing |
| *"devops with Kubernetes"* | 30 skills: K8s, Docker, CI/CD, Terraform, monitoring, cloud |
| *"ML engineer fine-tuning LLMs"* | Skills: LLM eval, prompt engineering, MLOps, fine-tuning, model deployment |

```bash
# One command installs everything
npx skills add vercel-labs/next-skills vercel-labs/agent-skills better-auth/skills ...
```

---

## Features

- **110k+ skills indexed** from skills.sh and GitHub, deduplicated and quality-scored
- **13 curated bundles** across 12 developer roles + task bundles
- **AI-powered matching** — describe your role in plain English, get the right bundle
- **Platform-aware install commands** for Claude Code, Cursor, GitHub Copilot, Continue.dev, and Universal
- **Tier 1 / Tier 2 system** — top skills stored fully in DB; long-tail fetched live from GitHub on demand
- **Paginated explore page** — browse all 1,000+ Tier 1 skills with page-number navigation
- **Zero lock-in** — every skill links back to its original GitHub source

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11+, SQLAlchemy (async) |
| Database | PostgreSQL (full-text search with `tsvector`) |
| Cache / Queue | Redis + Celery |
| AI / LLM | Groq (llama-3.3-70b) for skill tagging + bundle matching |
| Fonts | Inter · Plus Jakarta Sans · JetBrains Mono |

---

## Architecture

```
skills.sh scraper ─┐
                   ├──▶  raw skills ──▶  tagger.py (Groq LLM) ──▶  ingestion.py ──▶  PostgreSQL
GitHub crawler ────┘                                                                        │
                                                                                            ▼
                                                            bundle_generator.py ──▶  Bundle rows
                                                                                            │
                                                                                            ▼
                                                                              FastAPI ──▶  Next.js
```

### Tier System

| | Tier 1 (~1,500 skills) | Tier 2 (~110k skills) |
|---|---|---|
| **Storage** | Full row in `skills` table | Lightweight row in `skills_index` |
| **Content** | `raw_content` in DB | Fetched live from GitHub on demand |
| **Threshold** | `install_count ≥ 50` | Everything else |
| **API** | `/api/skills/{slug}` | `/api/live/{owner}/{repo}` |
| **Cache** | Permanent | Redis 24h TTL |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis
- [Groq API key](https://console.groq.com) (free)
- [GitHub Personal Access Token](https://github.com/settings/tokens) (free, read-only)

### 1. Clone

```bash
git clone https://github.com/Jeelislive/SkillPack.git
cd SkillPack
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, GROQ_API_KEY, GITHUB_TOKEN (see table below)

# Apply DB schema
psql $DATABASE_URL < db/schema.sql

# Run the API
python3 -m uvicorn api.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

npm install

# Create env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev   # http://localhost:3000
```

### 4. Run the Crawler (optional — populates the DB)

```bash
cd backend
source .venv/bin/activate

python3 run_crawl.py            # Full crawl: skills.sh + GitHub + tagging + bundles (~30 min)
python3 run_crawl.py --test     # Fast crawl: skills.sh only, no GitHub (~2 min)
python3 run_crawl.py bundles    # Re-generate bundles only (instant)
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SYNC_DATABASE_URL` | ✅ | — | Sync PostgreSQL URL for Celery workers |
| `GROQ_API_KEY` | ✅ | — | LLM for skill tagging and bundle matching |
| `GITHUB_TOKEN` | ✅ | — | GitHub API — read-only scope is enough |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Cache + Celery broker |
| `GITHUB_TOKEN_2` | — | `""` | Second GitHub token for higher rate limits |
| `ADMIN_TOKEN` | — | `changeme` | Protects `/api/crawl` admin endpoints |
| `TIER1_MIN_INSTALLS` | — | `50` | Min installs to qualify a skill for Tier 1 |
| `TIER1_MAX_SKILLS` | — | `25000` | Cap on Tier 1 DB size |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | URL of the FastAPI backend |

---

## Project Structure

```
SkillPack/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app entry point
│   │   └── routes/
│   │       ├── bundles.py       # GET /api/bundles
│   │       ├── skills.py        # GET /api/skills (paginated)
│   │       ├── search.py        # Full-text + AI bundle matching
│   │       ├── live.py          # Live-fetch Tier 2 skills
│   │       └── crawl.py         # Admin crawl triggers
│   ├── crawlers/
│   │   ├── skills_sh.py         # skills.sh RSC scraper
│   │   └── github_crawler.py    # GitHub Search API crawler
│   ├── pipeline/
│   │   ├── tagger.py            # Groq LLM skill classifier
│   │   ├── bundle_generator.py  # Role bundle builder
│   │   └── install_generator.py # Platform install command builder
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── ingestion.py         # Bulk upsert pipeline
│   │   └── schema.sql           # DB schema
│   ├── workers/                 # Celery async tasks
│   └── run_crawl.py             # CLI entry point
│
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx              # Hero + search + bundle cards
        │   ├── explore/page.tsx      # Paginated skills browser
        │   ├── bundle/[slug]/        # Bundle detail + platform selector
        │   └── skills/[...slug]/     # Individual skill detail
        ├── components/
        │   ├── BundleCard.tsx
        │   ├── InstallCommand.tsx
        │   └── PlatformSelector.tsx
        └── lib/
            └── api.ts               # Typed API client
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/bundles` | List all bundles |
| `GET` | `/api/bundles/{slug}` | Bundle detail + skills + install commands |
| `GET` | `/api/skills?limit=50&offset=0` | Paginated skill list |
| `GET` | `/api/skills/{slug}` | Individual skill detail |
| `GET` | `/api/skills/categories` | Skill counts by category |
| `GET` | `/api/search?q=...` | Full-text + fuzzy skill search |
| `GET` | `/api/search/match-bundle?q=...` | AI-powered role → bundle matching |
| `GET` | `/api/live/{owner}/{repo}` | Live-fetch Tier 2 skill from GitHub |

Interactive docs available at `http://localhost:8000/docs` when the backend is running.

---

## Supported Platforms

| Platform | Install prefix |
|---|---|
| **Claude Code** | `claude skills add` |
| **Cursor** | `cursor skills add` |
| **GitHub Copilot** | `gh copilot skills add` |
| **Continue.dev** | `continue skills add` |
| **Universal** | Raw GitHub URLs |

---

## Bundles

| Slug | Name | Category |
|---|---|---|
| `frontend` | Frontend Developer | UI, React, Next.js, CSS, accessibility |
| `backend` | Backend Developer | APIs, databases, auth, Node, Python |
| `fullstack` | Full Stack Developer | Frontend + backend + database |
| `devops` | DevOps Engineer | CI/CD, Docker, K8s, IaC, cloud |
| `ml-ai` | ML / AI Engineer | LLMs, MLOps, model training |
| `security` | Security Engineer | Auth, OAuth, vulnerability, secure coding |
| `database` | Database Engineer | SQL, NoSQL, query optimization |
| `testing` | QA / Testing Engineer | Unit, integration, E2E, TDD |
| `cloud` | Cloud Engineer | AWS, GCP, Azure, serverless |
| `mobile` | Mobile Developer | iOS, Android, React Native, Flutter |
| `data-science` | Data Scientist | Analysis, visualization, pipelines |
| `api-design` | API Designer | REST, GraphQL, OpenAPI |
| `build-landing-page` | Build a Landing Page | *(task bundle)* |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

1. Fork the repo
2. Create your branch: `git checkout -b feat/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push: `git push origin feat/amazing-feature`
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with ⚡ by <a href="https://github.com/Jeelislive">Jeel</a></sub>
</div>
