import json
import redis as _redis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from db.models import SkillRating, Skill, User
from api.deps import get_current_user
from config import get_settings

router = APIRouter()
settings = get_settings()

_RATING_TTL = 600  # 10 minutes

try:
    _cache = _redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=1
    )
    _cache.ping()
except Exception:
    _cache = None


def _agg_key(skill_id: int) -> str:
    return f"ratings:skill:{skill_id}"


def _get_agg(skill_id: int) -> dict | None:
    if not _cache:
        return None
    try:
        hit = _cache.get(_agg_key(skill_id))
        return json.loads(hit) if hit else None
    except Exception:
        return None


def _set_agg(skill_id: int, data: dict) -> None:
    if not _cache:
        return
    try:
        _cache.setex(_agg_key(skill_id), _RATING_TTL, json.dumps(data))
    except Exception:
        pass


class RatingBody(BaseModel):
    rating: int

    @field_validator("rating")
    @classmethod
    def check_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


async def _resolve_skill(slug: str, db: AsyncSession) -> Skill:
    result = await db.execute(select(Skill).where(Skill.slug == slug))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/{slug}/rate")
async def rate_skill(
    slug: str,
    body: RatingBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skill = await _resolve_skill(slug, db)

    result = await db.execute(
        select(SkillRating).where(
            SkillRating.user_id == user.id,
            SkillRating.skill_id == skill.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.rating = body.rating
    else:
        db.add(SkillRating(user_id=user.id, skill_id=skill.id, rating=body.rating))

    await db.commit()

    # Recompute and cache aggregate
    agg = await db.execute(
        select(func.avg(SkillRating.rating), func.count()).where(
            SkillRating.skill_id == skill.id
        )
    )
    avg_val, count_val = agg.one()
    agg_data = {"avg": round(float(avg_val or 0), 2), "count": count_val or 0}
    _set_agg(skill.id, agg_data)

    return {**agg_data, "your_rating": body.rating}


@router.get("/{slug}/ratings")
async def get_ratings(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    skill = await _resolve_skill(slug, db)

    cached = _get_agg(skill.id)
    if cached:
        return cached

    agg = await db.execute(
        select(func.avg(SkillRating.rating), func.count()).where(
            SkillRating.skill_id == skill.id
        )
    )
    avg_val, count_val = agg.one()
    data = {"avg": round(float(avg_val or 0), 2), "count": count_val or 0}
    _set_agg(skill.id, data)
    return data
