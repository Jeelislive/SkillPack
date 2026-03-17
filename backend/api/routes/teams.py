import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db.database import get_db
from db.models import Team, TeamMember, InstallEvent, Bundle, User
from api.deps import get_current_user, require_pro

router = APIRouter()


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50]


class TeamCreate(BaseModel):
    name: str
    slug: str | None = None


class CanonicalBundleSet(BaseModel):
    bundle_id: int


class MemberInvite(BaseModel):
    email: str


def _team_out(t: Team, members: list | None = None) -> dict:
    out = {
        "id": t.id, "slug": t.slug, "name": t.name,
        "owner_user_id": t.owner_user_id,
        "canonical_bundle_id": t.canonical_bundle_id,
        "is_active": t.is_active,
        "created_at": t.created_at,
    }
    if members is not None:
        out["members"] = members
    return out


@router.post("")
async def create_team(
    body: TeamCreate,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
):
    slug = body.slug or _slugify(body.name)
    existing = await db.execute(select(Team).where(Team.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Team slug already taken")

    team = Team(slug=slug, name=body.name, owner_user_id=user.id)
    db.add(team)
    await db.flush()

    db.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    await db.commit()
    await db.refresh(team)
    return _team_out(team)


@router.get("")
async def list_user_teams(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user.id, Team.is_active == True)
        .order_by(Team.created_at.desc())
    )
    return [_team_out(t) for t in result.scalars().all()]


@router.get("/{slug}")
async def get_team(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_member_team(slug, user.id, db)
    members_result = await db.execute(
        select(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .where(TeamMember.team_id == team.id)
    )
    members = [
        {"user_id": m.user_id, "role": m.role, "email": u.email, "name": u.name, "joined_at": m.joined_at}
        for m, u in members_result.all()
    ]
    return _team_out(team, members)


@router.put("/{slug}/canonical-bundle")
async def set_canonical_bundle(
    slug: str,
    body: CanonicalBundleSet,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_owner_team(slug, user.id, db)
    team.canonical_bundle_id = body.bundle_id
    await db.commit()
    return {"ok": True}


@router.post("/{slug}/members")
async def invite_member(
    slug: str,
    body: MemberInvite,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_owner_team(slug, user.id, db)

    target_result = await db.execute(select(User).where(User.email == body.email))
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="No user with that email found")

    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == target.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    db.add(TeamMember(team_id=team.id, user_id=target.id, role="member"))
    await db.commit()
    return {"ok": True}


@router.delete("/{slug}/members/{uid}")
async def remove_member(
    slug: str,
    uid: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_owner_team(slug, user.id, db)
    if uid == team.owner_user_id:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")
    await db.execute(
        delete(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == uid)
    )
    await db.commit()
    return {"ok": True}


@router.get("/{slug}/install-log")
async def install_log(
    slug: str,
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_member_team(slug, user.id, db)
    if not team.canonical_bundle_id:
        return []

    result = await db.execute(
        select(InstallEvent, User)
        .outerjoin(User, User.id == InstallEvent.user_id)
        .where(InstallEvent.bundle_id == team.canonical_bundle_id)
        .order_by(InstallEvent.created_at.desc())
        .limit(200)
    )
    return [
        {
            "platform": ev.platform,
            "created_at": ev.created_at,
            "user_email": u.email if u else None,
            "user_name":  u.name  if u else None,
        }
        for ev, u in result.all()
    ]


@router.get("/{slug}/install")
async def team_install_command(slug: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns canonical bundle install command (no auth required)."""
    team_result = await db.execute(
        select(Team).where(Team.slug == slug, Team.is_active == True)
    )
    team = team_result.scalar_one_or_none()
    if not team or not team.canonical_bundle_id:
        raise HTTPException(status_code=404, detail="Team or canonical bundle not found")

    from db.models import BundleCommand
    cmd_result = await db.execute(
        select(BundleCommand).where(
            BundleCommand.bundle_id == team.canonical_bundle_id,
            BundleCommand.platform == "claude_code",
        )
    )
    cmd = cmd_result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="No install command for this team")
    return {"command": cmd.command, "team": slug}


# ── helpers ─────────────────────────────────────────────────────────────────

async def _get_member_team(slug: str, user_id: str, db: AsyncSession) -> Team:
    result = await db.execute(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(Team.slug == slug, Team.is_active == True, TeamMember.user_id == user_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return team


async def _get_owner_team(slug: str, user_id: str, db: AsyncSession) -> Team:
    result = await db.execute(
        select(Team).where(
            Team.slug == slug, Team.is_active == True, Team.owner_user_id == user_id
        )
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=403, detail="Not the team owner")
    return team
