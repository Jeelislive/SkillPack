# SkillPack API Reference

## Route Prefixes
| Prefix | File | Notes |
|--------|------|-------|
| `/api/bundles` | `routes/bundles.py` | List/get bundles. Redis 5min cache. `install/{platform}` NOT cached (side-effect). |
| `/api/skills` | `routes/skills.py` | List with filters, get by `/{slug:path}` (path param for 3-part slugs) |
| `/api/search` | `routes/search.py` | FTS (tsvector), fuzzy (ILIKE), AI match → best bundle |
| `/api/live` | `routes/live.py` | Live-fetch Tier 2 skills from GitHub. Redis 24hr cache. |
| `/api/crawl` | `routes/crawl.py` | Admin-only. Header: `X-Admin-Token`. Triggers Celery tasks. |
| `/api/cron` | `routes/cron.py` | Vercel cron endpoints. Requires `X-Cron-Secret` header. |

## Critical Gotchas
- `redirect_slashes=False` on FastAPI app → list routes use `@router.get("")` NOT `"/"`
- All router files use `@router.get("")` for the list endpoint
- Install endpoint: `POST /api/bundles/install/{platform}/{slug}` - increments `install_count`, never cached

## Redis Cache Keys
```python
"bundles:list:{type_filter}"   # TTL 5 min (300s)
"bundles:slug:{slug}"          # TTL 5 min
"live:{owner}:{repo}"          # TTL 24 hr (86400s)
```
Cache NOT explicitly invalidated on write - expires naturally after TTL.

## Adding a New Route
1. Create `api/routes/my_route.py` with `router = APIRouter(prefix="/api/my-route", tags=["my-route"])`
2. Use `@router.get("")` for list, `@router.get("/{id}")` for detail
3. Register in `api/main.py`: `app.include_router(my_router)`
4. Use `Depends(get_db)` for DB, `Depends(get_redis)` for cache

## Authentication
- Admin endpoints: check `request.headers.get("X-Admin-Token") == settings.admin_token`
- Cron endpoints: check `X-Cron-Secret` header
- No user auth on public endpoints

## DB Session (Async)
```python
from db.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

## 3-Part Slug Handling
- skills.sh slugs: `owner/repo/skillId`
- API route: `@router.get("/{slug:path}")` - captures forward slashes
- Frontend: `[...slug]` catch-all → reassemble with `.join("/")`

## Supabase Connection (CRITICAL)
- Always Session Pooler: `aws-1-ap-southeast-1.pooler.supabase.com:5432`
- NOT Transaction Pooler: port 6543 breaks asyncpg prepared statements
- Both engines use `poolclass=NullPool` for Vercel serverless compatibility

## Search Endpoint Logic (`/api/search`)
1. Full-text: `tsvector` column match (fast, exact)
2. Fuzzy: `ILIKE '%query%'` fallback
3. Bundle match: `/api/search/match-bundle` → Groq picks best bundle → returns redirect slug

## Install Count
```python
# In /api/bundles/install/{platform}/{slug}:
bundle.install_count += 1
await db.commit()
# Also increments individual skill install_count for each skill in bundle
```

## Environment Variables (key ones)
| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | Async SQLAlchemy (postgresql+asyncpg://...) |
| `SYNC_DATABASE_URL` | Sync for Celery workers |
| `REDIS_URL` | Cache + Celery broker (default: redis://localhost:6379/0) |
| `GROQ_API_KEY` | LLM for tagging, bundle curation, search match |
| `ADMIN_TOKEN` | Protects /api/crawl (default: "changeme") |
| `CRON_SECRET` | Protects /api/cron |
