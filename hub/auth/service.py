"""Auth primitives — JWT access tokens, bcrypt passwords, API keys, refresh rotation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.models.refresh_token import RefreshToken

# ---------------- JWT ----------------


def create_jwt(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str) -> str:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return payload["sub"]


# ---------------- passwords ----------------


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


# ---------------- API keys ----------------


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    raw = "artic_" + secrets.token_urlsafe(32)
    return raw, hash_api_key(raw)


# ---------------- refresh tokens ----------------


@dataclass
class RefreshIssued:
    raw_token: str
    family_id: str
    expires_at: datetime


async def issue_refresh(
    db: AsyncSession, user_id: str, family_id: str | None = None
) -> RefreshIssued:
    """Create a new refresh token row and return the raw (once-only) token string."""
    raw = secrets.token_urlsafe(48)
    family = family_id or str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_EXPIRY_DAYS
    )
    db.add(
        RefreshToken(
            user_id=user_id,
            family_id=family,
            token_hash=_hash_refresh(raw),
            status="active",
            expires_at=expires_at,
        )
    )
    await db.commit()
    return RefreshIssued(raw_token=raw, family_id=family, expires_at=expires_at)


async def rotate_refresh(
    db: AsyncSession, raw_token: str
) -> tuple[str, RefreshIssued] | None:
    """Consume one refresh token and return (user_id, new RefreshIssued).

    If the presented token is already `used` → reuse detected → revoke the entire family.
    If `revoked` or `expired` → reject outright. Returns None on any failure.
    """
    token_hash = _hash_refresh(raw_token)
    row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    if row.status == "used":
        await _revoke_family(db, row.family_id)
        return None

    if row.status == "revoked":
        return None

    if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        row.status = "revoked"
        await db.commit()
        return None

    # Mark consumed; issue replacement in same family.
    row.status = "used"
    await db.commit()
    issued = await issue_refresh(db, row.user_id, family_id=row.family_id)
    return row.user_id, issued


async def revoke_family_by_token(db: AsyncSession, raw_token: str) -> None:
    token_hash = _hash_refresh(raw_token)
    row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if row:
        await _revoke_family(db, row.family_id)


def _hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def _revoke_family(db: AsyncSession, family_id: str) -> None:
    rows = (
        (
            await db.execute(
                select(RefreshToken).where(RefreshToken.family_id == family_id)
            )
        )
        .scalars()
        .all()
    )
    for r in rows:
        r.status = "revoked"
    await db.commit()
