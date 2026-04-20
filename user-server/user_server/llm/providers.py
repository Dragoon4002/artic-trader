"""Provider dispatch. Lazy-imports each SDK to keep cold-start cheap.

Each provider exposes `chat(messages, model, api_key) -> str`. Tests swap the
`PROVIDERS` dict with fakes to avoid network + SDK imports.
"""
from __future__ import annotations

from typing import Callable, Protocol

from shared.errors import AuthInvalid, Validation

from . import secrets_cache


class ProviderFn(Protocol):
    def __call__(self, messages: list[dict], model: str, api_key: str) -> str: ...


def _openai(messages: list[dict], model: str, api_key: str) -> str:
    from openai import OpenAI  # noqa: PLC0415

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content or ""


def _anthropic(messages: list[dict], model: str, api_key: str) -> str:
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=api_key)
    # Anthropic takes system separately; flatten for simplicity.
    system = next((m["content"] for m in messages if m.get("role") == "system"), None)
    others = [m for m in messages if m.get("role") != "system"]
    resp = client.messages.create(model=model, max_tokens=1024, system=system or "", messages=others)
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
    return "".join(parts)


def _deepseek(messages: list[dict], model: str, api_key: str) -> str:
    from openai import OpenAI  # noqa: PLC0415  DeepSeek is OpenAI-compatible

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content or ""


def _gemini(messages: list[dict], model: str, api_key: str) -> str:
    import google.generativeai as genai  # noqa: PLC0415

    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model)
    prompt = "\n".join(f"{x.get('role', 'user')}: {x.get('content', '')}" for x in messages)
    return m.generate_content(prompt).text or ""


PROVIDERS: dict[str, ProviderFn] = {
    "openai": _openai,
    "anthropic": _anthropic,
    "deepseek": _deepseek,
    "gemini": _gemini,
}

_KEY_FOR: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def dispatch(provider: str, messages: list[dict], model: str) -> str:
    fn = PROVIDERS.get(provider)
    if fn is None:
        raise Validation(f"unknown provider {provider!r}; one of {sorted(PROVIDERS)}")
    key_name = _KEY_FOR[provider]
    api_key = secrets_cache.get(key_name)
    if not api_key:
        raise AuthInvalid(f"{key_name} not in secrets cache; call /hub/secrets/refresh")
    return fn(messages, model, api_key)


def register(provider: str, fn: Callable[[list[dict], str, str], str], key_name: str | None = None) -> None:
    """Test hook: swap a provider implementation."""
    PROVIDERS[provider] = fn
    if key_name:
        _KEY_FOR[provider] = key_name
