"""
Live fetch route - fetches Tier 2 skills on demand from GitHub.
Results cached in Redis for 24 hours.
"""

import json
import hashlib
import httpx
import redis
from fastapi import APIRouter, HTTPException
from config import get_settings

router = APIRouter()
settings = get_settings()

CACHE_TTL = 86400  # 24 hours
GITHUB_RAW = "https://raw.githubusercontent.com"

try:
    cache = redis.from_url(settings.redis_url, decode_responses=True)
except Exception:
    cache = None


def _cache_key(slug: str) -> str:
    return f"live_skill:{hashlib.md5(slug.encode()).hexdigest()}"


@router.get("/{owner}/{repo}")
async def live_fetch_skill(owner: str, repo: str):
    """
    Live-fetch a Tier 2 skill's SKILL.md content from GitHub.
    Cached in Redis for 24 hours.
    """
    slug = f"{owner}/{repo}"
    key = _cache_key(slug)

    # Check cache first
    if cache:
        cached = cache.get(key)
        if cached:
            return {**json.loads(cached), "cached": True}

    # Fetch from GitHub
    content = None
    raw_url = None

    async with httpx.AsyncClient() as client:
        for branch in ["main", "master"]:
            for filename in ["SKILL.md", "skill.md", "skills.md"]:
                url = f"{GITHUB_RAW}/{slug}/{branch}/{filename}"
                try:
                    resp = await client.get(url, timeout=10)
                    if resp.status_code == 200:
                        content = resp.text
                        raw_url = url
                        break
                except Exception:
                    continue
            if content:
                break

    if not content:
        raise HTTPException(
            status_code=404,
            detail=f"SKILL.md not found for {slug}. The repo may not have a skill file."
        )

    result = {
        "slug": slug,
        "owner": owner,
        "repo": repo,
        "raw_url": raw_url,
        "raw_content": content,
        "install_command": f"npx skills add {slug}",
        "cached": False,
    }

    # Store in Redis cache
    if cache:
        try:
            cache.setex(key, CACHE_TTL, json.dumps(result))
        except Exception:
            pass

    return result
