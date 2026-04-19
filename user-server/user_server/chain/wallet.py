"""Wallet: load private key from disk keystore (prod) or env (dev).

KEK lives in the LLM secrets cache under key `WALLET_KEK`, pushed by hub at
wake via /hub/secrets/refresh. Missing KEK + no WALLET_PRIVATE_KEY env =>
chain signing disabled (signer raises AuthInvalid).
"""
from __future__ import annotations

import json
from pathlib import Path

from shared.errors import AuthInvalid

from ..config import settings
from ..llm import secrets_cache


def load_private_key() -> str:
    """Return hex private key (0x-prefixed). Raises AuthInvalid if unavailable."""
    if settings.WALLET_PRIVATE_KEY:
        return _normalize(settings.WALLET_PRIVATE_KEY)

    if not settings.KEYSTORE_PATH:
        raise AuthInvalid("WALLET_PRIVATE_KEY or KEYSTORE_PATH must be set")

    ks = Path(settings.KEYSTORE_PATH)
    if not ks.exists():
        raise AuthInvalid(f"keystore file missing at {ks}")

    kek = secrets_cache.get("WALLET_KEK")
    if not kek:
        raise AuthInvalid("WALLET_KEK not in secrets cache; hub must POST /hub/secrets/refresh")

    from eth_account import Account  # noqa: PLC0415

    data = json.loads(ks.read_text())
    key_bytes = Account.decrypt(data, kek)
    return _normalize(key_bytes.hex())


def _normalize(key: str) -> str:
    return key if key.startswith("0x") else "0x" + key


def address() -> str:
    from eth_account import Account  # noqa: PLC0415

    return Account.from_key(load_private_key()).address
