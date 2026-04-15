"""Auth logic: JWT, password hashing, API key management."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
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


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, hashed_key)."""
    raw = "artic_" + secrets.token_urlsafe(32)
    return raw, hash_api_key(raw)
