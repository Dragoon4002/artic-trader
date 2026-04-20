"""Session-key issuance + per-request signature verification.

Session keys are delegated by the user's wallet at /auth/verify time and used
to sign state-changing requests without re-prompting the wallet. Hub stores
the public half + a monotonic `last_nonce` to block replay.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.auth_session_key import AuthSessionKey

logger = logging.getLogger(__name__)


def canonical_request(
    method: str,
    path: str,
    body: bytes,
    session_id: str,
    nonce: int,
) -> bytes:
    """Exactly the payload the client signs — `json({...}, sort_keys=True)`."""
    body_sha256 = hashlib.sha256(body or b"").hexdigest()
    doc = {
        "method": method.upper(),
        "path": path,
        "body_sha256": body_sha256,
        "session_id": session_id,
        "nonce": int(nonce),
    }
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_session_signature(
    session_pub_b64: str,
    canonical: bytes,
    signature_b64: str,
) -> bool:
    """secp256k1 verify over sha256(canonical). Mirrors the web client."""
    try:
        from ecdsa import BadSignatureError, SECP256k1, VerifyingKey
        from ecdsa.util import sigdecode_string

        pub = base64.b64decode(session_pub_b64)
        if len(pub) != 33:
            return False
        sig = base64.b64decode(signature_b64)
        if len(sig) != 64:
            return False
        digest = hashlib.sha256(canonical).digest()
        vk = VerifyingKey.from_string(pub, curve=SECP256k1, hashfunc=hashlib.sha256)
        try:
            vk.verify_digest(sig, digest, sigdecode=sigdecode_string)
            return True
        except BadSignatureError:
            return False
    except Exception as exc:
        logger.warning("session sig verify failed: %s", exc)
        return False


async def load_active_session(
    db: AsyncSession, session_id: str, user_id: str
) -> AuthSessionKey | None:
    row = await db.execute(
        select(AuthSessionKey).where(
            AuthSessionKey.id == session_id,
            AuthSessionKey.user_id == user_id,
        )
    )
    sess = row.scalar_one_or_none()
    if not sess or sess.revoked_at is not None:
        return None
    if sess.expires_at <= datetime.now(timezone.utc):
        return None
    return sess


async def bump_nonce_atomic(
    db: AsyncSession, sess: AuthSessionKey, presented_nonce: int
) -> bool:
    """Reject if presented_nonce <= last_nonce; otherwise atomically bump."""
    if presented_nonce <= sess.last_nonce:
        return False
    sess.last_nonce = presented_nonce
    await db.commit()
    return True


async def revoke_session(db: AsyncSession, sess: AuthSessionKey) -> None:
    sess.revoked_at = datetime.now(timezone.utc)
    await db.commit()
