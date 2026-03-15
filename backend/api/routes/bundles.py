from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from db.database import get_db
from db.models import Bundle, BundleCommand, Skill

router = APIRouter()


@router.get("")
async def list_bundles(
    type: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Bundle).where(Bundle.is_active == True)
    if type:
        q = q.where(Bundle.type == type)
    if category:
        q = q.where(Bundle.category == category)
    q = q.order_by(Bundle.is_featured.desc(), Bundle.install_count.desc())
    result = await db.execute(q)
    bundles = result.scalars().all()
    return [_bundle_summary(b) for b in bundles]


@router.get("/{slug}")
async def get_bundle(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bundle).where(Bundle.slug == slug, Bundle.is_active == True)
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    # Fetch commands
    cmd_result = await db.execute(
        select(BundleCommand).where(BundleCommand.bundle_id == bundle.id)
    )
    commands = {c.platform: c.command for c in cmd_result.scalars().all()}

    # Fetch skills
    skills = []
    if bundle.skill_ids:
        sk_result = await db.execute(
            select(Skill).where(Skill.id.in_(bundle.skill_ids))
        )
        skill_objs = {s.id: s for s in sk_result.scalars().all()}
        # preserve order
        skills = [_skill_summary(skill_objs[sid]) for sid in bundle.skill_ids if sid in skill_objs]

    return {
        **_bundle_summary(bundle),
        "skills": skills,
        "commands": commands,
    }


@router.get("/{slug}/install/{platform}")
async def get_install_command(
    slug: str,
    platform: str,
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
