"""FastAPI auth dependencies."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models.user import User
from . import service, session as session_svc


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """JWT from Authorization, fall back to X-API-Key."""
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

    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        hashed = service.hash_api_key(api_key)
        result = await db.execute(select(User).where(User.api_key_hash == hashed))
        user = result.scalar_one_or_none()
        if user:
            return user

    raise HTTPException(status_code=401, detail="Missing or invalid credentials")


async def require_session_key(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Enforce session-key signed request for state-changing endpoints."""
    session_id = request.headers.get("X-Session-Id")
    raw_nonce = request.headers.get("X-Session-Nonce")
    signature = request.headers.get("X-Session-Sig")

    if not (session_id and raw_nonce and signature):
        raise HTTPException(status_code=401, detail="Session signature required")

    try:
        nonce = int(raw_nonce)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Session-Nonce")

    sess = await session_svc.load_active_session(db, session_id, user.id)
    if not sess:
        raise HTTPException(status_code=401, detail="Session expired or revoked")

    body = await request.body()
    canonical = session_svc.canonical_request(
        method=request.method,
        path=request.url.path,
        body=body,
        session_id=session_id,
        nonce=nonce,
    )
    if not session_svc.verify_session_signature(sess.session_pub, canonical, signature):
        raise HTTPException(status_code=401, detail="Invalid session signature")

    if not await session_svc.bump_nonce_atomic(db, sess, nonce):
        raise HTTPException(status_code=401, detail="Nonce replay rejected")

    return user
