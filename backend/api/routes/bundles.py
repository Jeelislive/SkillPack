import json
import redis as _redis
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from db.database import get_db
from db.models import Bundle, BundleCommand, Skill, InstallEvent
from config import get_settings

router = APIRouter()
settings = get_settings()

_LIST_TTL = 300    # 5 minutes
_DETAIL_TTL = 300  # 5 minutes

try:
    _cache = _redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=1
    )
    _cache.ping()
except Exception:
    _cache = None


def _list_key(type_: str | None, category: str | None) -> str:
    return f"bundles:list:{type_ or '*'}:{category or '*'}"


def _slug_key(slug: str) -> str:
    return f"bundles:slug:{slug}"


def _cache_get(key: str):
    if not _cache:
        return None
    try:
        hit = _cache.get(key)
        return json.loads(hit) if hit else None
    except Exception:
        return None


def _cache_set(key: str, data, ttl: int) -> None:
    if not _cache:
        return
    try:
        _cache.setex(key, ttl, json.dumps(data))
    except Exception:
        pass


@router.get("")
async def list_bundles(
    type: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    key = _list_key(type, category)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    from sqlalchemy import or_
    q = select(Bundle).where(
        Bundle.is_active == True,
        or_(Bundle.owner_user_id == None, Bundle.is_public == True),
    )
    if type:
        q = q.where(Bundle.type == type)
    if category:
        q = q.where(Bundle.category == category)
    q = q.order_by(Bundle.is_featured.desc(), Bundle.install_count.desc())
    result = await db.execute(q)
    bundles = result.scalars().all()
    data = [_bundle_summary(b) for b in bundles]

    _cache_set(key, data, _LIST_TTL)
    return data


@router.get("/{slug}")
async def get_bundle(slug: str, db: AsyncSession = Depends(get_db)):
    key = _slug_key(slug)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    result = await db.execute(
        select(Bundle)
        .options(selectinload(Bundle.commands))
        .where(Bundle.slug == slug, Bundle.is_active == True)
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    # Commands already loaded via selectinload — no extra round-trip
    commands = {c.platform: c.command for c in bundle.commands}

    # Fetch skills
    skills = []
    if bundle.skill_ids:
        sk_result = await db.execute(
            select(Skill).where(Skill.id.in_(bundle.skill_ids))
        )
        skill_objs = {s.id: s for s in sk_result.scalars().all()}
        # preserve order
        skills = [_skill_summary(skill_objs[sid]) for sid in bundle.skill_ids if sid in skill_objs]

    data = {
        **_bundle_summary(bundle),
        "skills": skills,
        "commands": commands,
    }
    _cache_set(key, data, _DETAIL_TTL)
    return data


@router.get("/{slug}/install/{platform}")
async def get_install_command(
    slug: str,
    platform: str,
    x_user_id: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Return the install command for a specific bundle + platform."""
    valid_platforms = ["claude_code", "cursor", "copilot", "continue", "universal"]
    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"Platform must be one of {valid_platforms}")

    result = await db.execute(select(Bundle).where(Bundle.slug == slug))
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    cmd_result = await db.execute(
        select(BundleCommand).where(
            BundleCommand.bundle_id == bundle.id,
            BundleCommand.platform == platform,
        )
    )
    cmd = cmd_result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found for this platform")

    # Track install count
    await db.execute(
        update(Bundle).where(Bundle.id == bundle.id).values(install_count=Bundle.install_count + 1)
    )
    # Record granular install event when user is authenticated
    if x_user_id:
        db.add(InstallEvent(user_id=x_user_id, bundle_id=bundle.id, platform=platform))
    await db.commit()

    return {"platform": platform, "command": cmd.command, "bundle": slug}


def _bundle_summary(b: Bundle) -> dict:
    return {
        "id": b.id,
        "slug": b.slug,
        "name": b.name,
        "description": b.description,
        "type": b.type,
        "category": b.category,
        "skill_count": b.skill_count,
        "install_count": b.install_count,
        "is_featured": b.is_featured,
    }


def _skill_summary(s: Skill) -> dict:
    return {
        "id": s.id,
        "slug": s.slug,
        "name": s.name,
        "description": s.description,
        "primary_category": s.primary_category,
        "tags": s.tags,
        "platforms": s.platforms,
        "install_command": s.install_command,
        "quality_score": float(s.quality_score or 0),
        "popularity_score": float(s.popularity_score or 0),
        "install_count": s.install_count,
        "source_url": s.source_url,
    }
