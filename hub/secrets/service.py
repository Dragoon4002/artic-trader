"""User secret management — write-only; plaintext never returned to client.

Hub stores AES-GCM ciphertext; decrypt happens in-process only during `secrets.push`
on wake. Agent-scoped overrides moved to user-server (see hub/deprecated/).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user
from ..db.base import get_session
from ..db.models.secret import UserSecret
from ..db.models.user import User
from . import crypto

router = APIRouter(prefix="/api/v1/secrets", tags=["secrets"])


class SecretWrite(BaseModel):
    key_name: str
    value: str  # plaintext — hub encrypts before storing


@router.post("")
async def put_secret(
    body: SecretWrite,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Create/update a user secret. Body carries plaintext over TLS; server encrypts."""
    ciphertext = crypto.encrypt(body.value)
    existing = (
        await db.execute(
            select(UserSecret).where(
                UserSecret.user_id == user.id, UserSecret.key_name == body.key_name
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.encrypted_value = ciphertext
    else:
        db.add(
            UserSecret(
                user_id=user.id, key_name=body.key_name, encrypted_value=ciphertext
            )
        )
    await db.commit()
    return {"ok": True, "key_name": body.key_name}


@router.get("")
async def list_secrets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Return key names only — never plaintext, never ciphertext."""
    rows = (
        await db.execute(
            select(UserSecret.key_name).where(UserSecret.user_id == user.id)
        )
    ).all()
    return {"keys": [r[0] for r in rows]}


@router.delete("/{key_name}")
async def delete_secret(
    key_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    row = (
        await db.execute(
            select(UserSecret).where(
                UserSecret.user_id == user.id, UserSecret.key_name == key_name
            )
        )
    ).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
    return {"ok": True}
