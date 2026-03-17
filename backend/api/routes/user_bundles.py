import re
import random
import string
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from db.database import get_db
from db.models import Bundle, BundleCommand, Skill, User
from api.deps import get_current_user
from pipeline.install_generator import InstallGenerator

router = APIRouter()

_PLATFORMS = ["claude_code", "cursor", "copilot", "continue", "universal"]


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40]


def _make_slug(user_id: str, name: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{user_id[:8]}-{_slugify(name)}-{suffix}"


class BundleCreate(BaseModel):
    name: str
    description: str = ""
    skill_ids: list[int] = []
    is_public: bool = True


class BundleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    skill_ids: list[int] | None = None
    is_public: bool | None = None


def _bundle_out(b: Bundle, commands: dict | None = None) -> dict:
    out = {
        "id":           b.id,
        "slug":         b.slug,
        "name":         b.name,
        "description":  b.description,
        "type":         b.type,
        "skill_count":  b.skill_count,
        "install_count": b.install_count,
        "is_public":    b.is_public,
        "is_featured":  b.is_featured,
        "created_at":   b.created_at,
    }
    if commands is not None:
        out["commands"] = commands
    return out


async def _generate_commands(db: AsyncSession, bundle: Bundle, skill_ids: list[int]) -> None:
    """Delete existing commands and regenerate for all platforms."""
    await db.execute(delete(BundleCommand).where(BundleCommand.bundle_id == bundle.id))

    if not skill_ids:
        return

    result = await db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
    skill_objs = result.scalars().all()

    gen = InstallGenerator()
    for platform in _PLATFORMS:
        cmd = gen.generate(list(skill_objs), platform, bundle.slug)
        if cmd:
            db.add(BundleCommand(bundle_id=bundle.id, platform=platform, command=cmd))


@router.post("/bundles")
async def create_bundle(
    body: BundleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Tier enforcement for private bundles
    if not body.is_public and user.tier != "pro":
        count = await db.scalar(
            select(func.count()).where(
                Bundle.owner_user_id == user.id,
                Bundle.is_public == False,
                Bundle.is_active == True,
            )
        )
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free plan limited to 3 private bundles. Upgrade to Pro.",
            )

    slug = _make_slug(user.id, body.name)
    bundle = Bundle(
        slug          = slug,
        name          = body.name,
        description   = body.description,
        type          = "custom",
        skill_ids     = body.skill_ids,
        skill_count   = len(body.skill_ids),
        is_public     = body.is_public,
        owner_user_id = user.id,
        created_by    = user.id,
    )
    db.add(bundle)
    await db.flush()   # get bundle.id

    await _generate_commands(db, bundle, body.skill_ids)
    await db.commit()
    await db.refresh(bundle)

    result = await db.execute(
        select(BundleCommand).where(BundleCommand.bundle_id == bundle.id)
    )
    commands = {c.platform: c.command for c in result.scalars().all()}
    return _bundle_out(bundle, commands)


@router.get("/bundles")
async def list_user_bundles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bundle).where(
            Bundle.owner_user_id == user.id,
            Bundle.is_active == True,
        ).order_by(Bundle.created_at.desc())
    )
    return [_bundle_out(b) for b in result.scalars().all()]


@router.get("/bundles/{slug}")
async def get_user_bundle(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bundle).where(
            Bundle.slug == slug,
            Bundle.owner_user_id == user.id,
            Bundle.is_active == True,
        )
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    cmd_result = await db.execute(
        select(BundleCommand).where(BundleCommand.bundle_id == bundle.id)
    )
    commands = {c.platform: c.command for c in cmd_result.scalars().all()}
    return _bundle_out(bundle, commands)


@router.put("/bundles/{slug}")
async def update_user_bundle(
    slug: str,
    body: BundleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bundle).where(
            Bundle.slug == slug,
            Bundle.owner_user_id == user.id,
            Bundle.is_active == True,
        )
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    # Tier check when making private
    if body.is_public is False and bundle.is_public and user.tier != "pro":
        count = await db.scalar(
            select(func.count()).where(
                Bundle.owner_user_id == user.id,
                Bundle.is_public == False,
                Bundle.is_active == True,
            )
        )
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free plan limited to 3 private bundles. Upgrade to Pro.",
            )

    if body.name is not None:
        bundle.name = body.name
    if body.description is not None:
        bundle.description = body.description
    if body.is_public is not None:
        bundle.is_public = body.is_public
    if body.skill_ids is not None:
        bundle.skill_ids  = body.skill_ids
        bundle.skill_count = len(body.skill_ids)
        await _generate_commands(db, bundle, body.skill_ids)

    await db.commit()
    await db.refresh(bundle)

    cmd_result = await db.execute(
        select(BundleCommand).where(BundleCommand.bundle_id == bundle.id)
    )
    commands = {c.platform: c.command for c in cmd_result.scalars().all()}
    return _bundle_out(bundle, commands)


@router.delete("/bundles/{slug}")
async def delete_user_bundle(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bundle).where(
            Bundle.slug == slug,
            Bundle.owner_user_id == user.id,
            Bundle.is_active == True,
        )
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    bundle.is_active = False
    await db.commit()
    return {"ok": True}
