from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db.database import get_db
from db.models import UserSave, Skill, Bundle, User
from api.deps import get_current_user

router = APIRouter()


def _skill_out(s: Skill) -> dict:
    return {
        "id": s.id, "slug": s.slug, "name": s.name,
        "description": s.description, "primary_category": s.primary_category,
        "tags": s.tags, "platforms": s.platforms,
        "install_command": s.install_command,
        "quality_score": float(s.quality_score or 0),
        "install_count": s.install_count,
        "source_url": s.source_url,
    }


def _bundle_out(b: Bundle) -> dict:
    return {
        "id": b.id, "slug": b.slug, "name": b.name,
        "description": b.description, "type": b.type,
        "skill_count": b.skill_count, "install_count": b.install_count,
        "is_featured": b.is_featured,
    }


@router.get("")
async def list_saves(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSave).where(UserSave.user_id == user.id)
        .order_by(UserSave.created_at.desc())
    )
    saves = result.scalars().all()

    skill_ids  = [s.skill_id  for s in saves if s.skill_id]
    bundle_ids = [s.bundle_id for s in saves if s.bundle_id]

    skills_map: dict = {}
    if skill_ids:
        sk = await db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
        skills_map = {s.id: s for s in sk.scalars().all()}

    bundles_map: dict = {}
    if bundle_ids:
        bk = await db.execute(select(Bundle).where(Bundle.id.in_(bundle_ids)))
        bundles_map = {b.id: b for b in bk.scalars().all()}

    return {
        "skills":  [_skill_out(skills_map[s.skill_id])   for s in saves if s.skill_id  and s.skill_id  in skills_map],
        "bundles": [_bundle_out(bundles_map[s.bundle_id]) for s in saves if s.bundle_id and s.bundle_id in bundles_map],
        "saved_skill_ids":  list(skill_ids),
        "saved_bundle_ids": list(bundle_ids),
    }


@router.post("/skill/{skill_id}")
async def save_skill(
    skill_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserSave).where(UserSave.user_id == user.id, UserSave.skill_id == skill_id)
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "saved": True}

    db.add(UserSave(user_id=user.id, skill_id=skill_id))
    await db.commit()
    return {"ok": True, "saved": True}


@router.delete("/skill/{skill_id}")
async def unsave_skill(
    skill_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(UserSave).where(UserSave.user_id == user.id, UserSave.skill_id == skill_id)
    )
    await db.commit()
    return {"ok": True, "saved": False}


@router.post("/bundle/{bundle_id}")
async def save_bundle(
    bundle_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserSave).where(UserSave.user_id == user.id, UserSave.bundle_id == bundle_id)
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "saved": True}

    db.add(UserSave(user_id=user.id, bundle_id=bundle_id))
    await db.commit()
    return {"ok": True, "saved": True}


@router.delete("/bundle/{bundle_id}")
async def unsave_bundle(
    bundle_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(UserSave).where(UserSave.user_id == user.id, UserSave.bundle_id == bundle_id)
    )
    await db.commit()
    return {"ok": True, "saved": False}
