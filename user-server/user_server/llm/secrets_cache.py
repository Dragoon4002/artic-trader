"""In-memory LLM/CEX key cache. Populated by A7 /hub/secrets/refresh.

Never persisted, never logged. Wiped on process exit (standard dict lifetime).
Key names match docs/alpha/data-model.md user_secrets.key_name
(e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY).
"""
from __future__ import annotations

_cache: dict[str, str] = {}


def put(key_name: str, value: str) -> None:
    _cache[key_name] = value


def get(key_name: str) -> str | None:
    return _cache.get(key_name)


def put_many(items: dict[str, str]) -> None:
    _cache.update(items)


def clear() -> None:
    _cache.clear()


def known_keys() -> list[str]:
    return sorted(_cache.keys())
