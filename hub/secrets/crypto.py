"""AES-GCM wrapper — KEK-derived. KEK held in `settings.KEK` (base64 32-byte key).

The KEK never touches Postgres. `user_secrets.encrypted_value` stores:
  base64(nonce || ciphertext || tag) — all concatenated.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import settings

_NONCE_LEN = 12


def _kek() -> bytes:
    if not settings.KEK:
        raise RuntimeError("KEK not set")
    key = base64.b64decode(settings.KEK)
    if len(key) != 32:
        raise RuntimeError("KEK must be 32 bytes base64-encoded")
    return key


def encrypt(plaintext: str, aad: bytes = b"") -> str:
    """Return base64(nonce||ciphertext||tag)."""
    cipher = AESGCM(_kek())
    nonce = os.urandom(_NONCE_LEN)
    blob = cipher.encrypt(nonce, plaintext.encode(), aad)
    return base64.b64encode(nonce + blob).decode()


def decrypt(b64_blob: str, aad: bytes = b"") -> str:
    raw = base64.b64decode(b64_blob)
    nonce, blob = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
    return AESGCM(_kek()).decrypt(nonce, blob, aad).decode()
