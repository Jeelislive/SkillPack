from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import User


async def get_current_user(
    x_user_id: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve user from NextAuth session header. Raises 401 if missing."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    result = await db.execute(select(User).where(User.id == x_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found. Call /api/user/sync first.")
    return user


async def require_pro(user: User = Depends(get_current_user)) -> User:
    if user.tier != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required")
    return user
