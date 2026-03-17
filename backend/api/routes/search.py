"""
Search route - handles:
1. Keyword search (pg_trgm full-text)
2. "Describe your role" → returns best matching bundle
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from openai import AsyncOpenAI
from db.database import get_db
from db.models import Skill, Bundle
from config import get_settings

router = APIRouter()
settings = get_settings()

groq = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url=settings.groq_base_url,
)

MATCH_PROMPT = """You are matching a user's role description to a skill bundle category.

User said: "{query}"

Available bundle slugs: {slugs}

Return ONLY the single best matching slug from the list above, nothing else.
If nothing matches, return "fullstack"."""


@router.get("")
async def search_skills(
    q: str = Query(..., min_length=2),
    category: str | None = None,
    platform: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text + trigram search across skill name, description, tags."""
    # Use PostgreSQL full-text search
    fts_query = text("""
        SELECT id FROM skills
        WHERE is_active = true AND tier = 1
        AND (
            to_tsvector('english',
                COALESCE(name, '') || ' ' ||
                COALESCE(description, '') || ' ' ||
                COALESCE(array_to_string(tags, ' '), '') || ' ' ||
                COALESCE(primary_category, '')
            ) @@ plainto_tsquery('english', :q)
            OR name ILIKE :fuzzy
            OR description ILIKE :fuzzy
        )
        ORDER BY (quality_score * 0.6 + popularity_score * 0.4) DESC
        LIMIT :limit
    """)

    result = await db.execute(
        fts_query,
        {"q": q, "fuzzy": f"%{q}%", "limit": limit}
    )
    ids = [row[0] for row in result.all()]

    if not ids:
        return {"results": [], "query": q}

    skills_result = await db.execute(
        select(Skill).where(Skill.id.in_(ids))
    )
    skills = skills_result.scalars().all()

    # Preserve relevance order
    skill_map = {s.id: s for s in skills}
    ordered = [skill_map[i] for i in ids if i in skill_map]

    return {
        "query": q,
        "results": [_fmt(s) for s in ordered],
    }


@router.get("/match-bundle")
async def match_bundle(
    q: str = Query(..., min_length=3, description="Describe what you build or your role"),
    db: AsyncSession = Depends(get_db),
):
    """
    Takes a natural language description and returns the best matching bundle.
    Uses Groq to classify the query into a bundle slug.
    """
    # Get all active bundle slugs
    result = await db.execute(
        select(Bundle.slug, Bundle.name).where(Bundle.is_active == True)
    )
    bundles = result.all()
    slugs = [b[0] for b in bundles]
    slug_names = {b[0]: b[1] for b in bundles}

    if not slugs:
        return {"query": q, "bundle": None}

    try:
        prompt = MATCH_PROMPT.format(query=q, slugs=", ".join(slugs))
        resp = await groq.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20,
        )
        matched_slug = resp.choices[0].message.content.strip().lower()

        # Validate it's a real slug
        if matched_slug not in slugs:
            # Fallback: simple keyword match
            q_lower = q.lower()
            matched_slug = next(
                (s for s in slugs if s in q_lower or q_lower in s),
                "fullstack"
            )

    except Exception:
        # Fallback: keyword matching without AI
        q_lower = q.lower()
        matched_slug = next(
            (s for s in slugs if s in q_lower or q_lower in s),
            "fullstack"
        )

    return {
        "query": q,
        "matched_bundle": matched_slug,
        "bundle_name": slug_names.get(matched_slug, matched_slug),
        "url": f"/bundle/{matched_slug}",
    }


def _fmt(s: Skill) -> dict:
    return {
        "slug": s.slug,
        "name": s.name,
        "description": s.description,
        "primary_category": s.primary_category,
        "tags": s.tags,
        "platforms": s.platforms,
        "install_command": s.install_command,
        "quality_score": float(s.quality_score or 0),
        "install_count": s.install_count,
        "source_url": s.source_url,
    }
