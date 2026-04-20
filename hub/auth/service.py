"""Auth primitives: JWT, API key hashing, wallet-auth message builder + nonce."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from ..config import settings


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str) -> str:
    """Return user_id or raise."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return payload["sub"]


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, hashed_key)."""
    raw = "artic_" + secrets.token_urlsafe(32)
    return raw, hash_api_key(raw)


# ── Wallet auth helpers ─────────────────────────────────────────────────────


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def build_signin_message(
    *,
    chain: str,
    address: str,
    nonce: str,
    session_pub: str,
    session_scope: str,
    issued_at: datetime,
    session_expires_at: datetime,
) -> str:
    """Canonical sign-in message. Client signs it verbatim."""
    return (
        f"{settings.AUTH_MESSAGE_DOMAIN} wants you to sign in with your {chain} account:\n"
        f"{address}\n"
        f"\n"
        f"Session public key: {session_pub}\n"
        f"Scope: {session_scope}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at.isoformat()}\n"
        f"Expires At: {session_expires_at.isoformat()}"
    )
