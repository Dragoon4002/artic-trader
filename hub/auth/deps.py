"""FastAPI auth dependencies."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models.user import User
from . import service


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Try JWT from Authorization header, then API key from X-API-Key."""
    # JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            user_id = service.verify_jwt(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    # API key
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        hashed = service.hash_api_key(api_key)
        result = await db.execute(select(User).where(User.api_key_hash == hashed))
        user = result.scalar_one_or_none()
        if user:
            return user

    raise HTTPException(status_code=401, detail="Missing or invalid credentials")
