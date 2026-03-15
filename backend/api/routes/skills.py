from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from db.database import get_db
from db.models import Skill

router = APIRouter()


@router.get("")
async def list_skills(
    category: str | None = None,
    platform: str | None = None,
    min_quality: float = 0,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    base = select(Skill).where(Skill.is_active == True, Skill.tier == 1)

    if category:
        base = base.where(Skill.primary_category == category)
    if platform:
        base = base.where(Skill.platforms.contains([platform]))
    if min_quality:
        base = base.where(Skill.quality_score >= min_quality)

    # Total count (same filters, no pagination)
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    # Paginated data
    data_q = base.order_by(
        (Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc()
    ).offset(offset).limit(limit)

    result = await db.execute(data_q)
    skills = result.scalars().all()

    return {
        "items": [_skill_detail(s) for s in skills],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Skill.primary_category, func.count(Skill.id).label("count"))
        .where(Skill.is_active == True, Skill.tier == 1, Skill.primary_category != None)
        .group_by(Skill.primary_category)
        .order_by(func.count(Skill.id).desc())
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]


@router.get("/{slug:path}")
async def get_skill(slug: str, db: AsyncSession = Depends(get_db)):
    # Handles both 2-part (owner/repo) and 3-part (owner/repo/skillId) slugs
    result = await db.execute(select(Skill).where(Skill.slug == slug))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in DB. Use /api/live/ to fetch it.")
    return _skill_detail(skill, include_content=True)


def _skill_detail(s: Skill, include_content: bool = False) -> dict:
    d = {
        "id": s.id,
        "slug": s.slug,
        "name": s.name,
        "description": s.description,
        "primary_category": s.primary_category,
        "sub_categories": s.sub_categories,
        "tags": s.tags,
        "role_keywords": s.role_keywords,
        "task_keywords": s.task_keywords,
        "platforms": s.platforms,
        "install_command": s.install_command,
        "quality_score": float(s.quality_score or 0),
        "popularity_score": float(s.popularity_score or 0),
        "install_count": s.install_count,
        "github_stars": s.github_stars,
        "source_url": s.source_url,
        "raw_url": s.raw_url,
        "tier": s.tier,
        "last_crawled_at": s.last_crawled_at.isoformat() if s.last_crawled_at else None,
    }
    if include_content:
        d["raw_content"] = s.raw_content
    return d
