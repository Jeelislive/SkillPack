from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import User
from api.deps import get_current_user

router = APIRouter()


@router.post("/sync")
async def sync_user(
    x_user_id: str = Header(default=""),
    x_user_email: str = Header(default=""),
    x_user_name: str = Header(default=""),
    x_user_image: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Upsert user from NextAuth session. Called by frontend on every authenticated page load."""
    if not x_user_id or not x_user_email:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="X-User-Id and X-User-Email headers required")

    result = await db.execute(select(User).where(User.id == x_user_id))
    user = result.scalar_one_or_none()

    if user:
        user.email      = x_user_email
        user.name       = x_user_name or user.name
        user.avatar_url = x_user_image or user.avatar_url
    else:
        user = User(
            id         = x_user_id,
            email      = x_user_email,
            name       = x_user_name or None,
            avatar_url = x_user_image or None,
            tier       = "free",
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name, "tier": user.tier}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id":         user.id,
        "email":      user.email,
        "name":       user.name,
        "avatar_url": user.avatar_url,
        "tier":       user.tier,
        "created_at": user.created_at,
    }
