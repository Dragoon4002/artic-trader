"""
Copilot chat endpoint — multi-model: OpenAI, Claude, DeepSeek.
Supports model selection via model ID; routes to the appropriate API.
"""
import os
from typing import Optional, List, Literal

Provider = Literal["openai", "anthropic", "deepseek", "gemini"]

# Model ID -> (provider, api_model_name)
CHAT_MODEL_MAP: dict[str, tuple[Provider, str]] = {
    # OpenAI (2-3 models)
    "gpt-4o": ("openai", "gpt-4o"),
    "gpt-4o-mini": ("openai", "gpt-4o-mini"),
    "gpt-4-turbo": ("openai", "gpt-4-turbo"),
    # Claude (2-3 models)
    "claude-sonnet-4-5": ("anthropic", "claude-sonnet-4-5"),
    "claude-3-5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "claude-3-5-haiku": ("anthropic", "claude-3-5-haiku-20241022"),
    # DeepSeek (2-3 models)
    "deepseek-chat": ("deepseek", "deepseek-chat"),
    "deepseek-reasoner": ("deepseek", "deepseek-reasoner"),
    "deepseek-r1": ("deepseek", "deepseek-r1"),  # alias; may fallback to deepseek-reasoner if unavailable
    # Gemini
    "gemini-2.0-flash": ("gemini", "gemini-2.0-flash"),
    "gemini-2.5-pro": ("gemini", "gemini-2.5-pro"),
    "gemini-2.5-flash": ("gemini", "gemini-2.5-flash"),
}

COPILOT_SYSTEM = """You are a retail trading copilot. Your job is to understand the user's intent and help them plan trades by gathering key information. Be concise and friendly. Ask one or two questions at a time—don't overwhelm.

When relevant, cover these six areas (ask naturally in conversation; don't list them all at once):
1. **Where do they want to trade?** — Crypto, global/forex, or Indian markets?
2. **What assets?** — Specific symbols, pairs, or sectors (e.g. BTC, ETH, Nifty 50, EUR/USD).
3. **Any strategy in mind?** — e.g. DCA, grid bot, swing, scalping, or "not sure".
4. **How much do they want to invest?** — Amount or range (you can use INR, USD, or relative terms).
5. **Risk tolerance?** — Conservative, moderate, or aggressive; max drawdown or loss they can accept.
6. **News / alpha sources?** — Any sources they want to use for triggers or alpha (e.g. Twitter, specific newsletters, earnings, macro).

If the user's message already answers some of these, acknowledge it and ask the next relevant question. Once you have enough context, summarize their trade plan and suggest next steps (e.g. open Trade Simulation, pick a strategy, set alerts)."""


def _get_api_key(provider: Provider) -> Optional[str]:
    keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    return (os.getenv(keys[provider]) or "").strip() or None


def chat_completion(
    messages: List[dict],
    model_id: str,
) -> str:
    """
    Run chat completion using the specified model ID.
    Returns the assistant's reply text.
    """
    entry = CHAT_MODEL_MAP.get(model_id)
    if not entry:
        raise ValueError(f"Unknown model: {model_id}. Supported: {list(CHAT_MODEL_MAP.keys())}")
    provider, api_model = entry
    api_key = _get_api_key(provider)
    if not api_key:
        raise ValueError(
            f"API key not set for {provider}. "
            f"Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY in .env"
        )

    # Normalize messages
    chat_messages = []
    for m in messages:
        role = (m.get("role") or "user").lower()
        content = m.get("content") or ""
        if isinstance(content, str):
            chat_messages.append({"role": role, "content": content})
        else:
            chat_messages.append({"role": role, "content": str(content)})

    if provider == "openai":
        return _chat_openai(api_key, api_model, chat_messages)
    if provider == "deepseek":
        return _chat_deepseek(api_key, api_model, chat_messages)
    if provider == "gemini":
        return _chat_gemini(api_key, api_model, chat_messages)
    return _chat_anthropic(api_key, api_model, chat_messages)


def _chat_openai(api_key: str, model: str, messages: List[dict]) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    system = {"role": "system", "content": COPILOT_SYSTEM}
    msgs = [system] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("role") != "system"]
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        max_tokens=1024,
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def _chat_deepseek(api_key: str, model: str, messages: List[dict]) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    system = {"role": "system", "content": COPILOT_SYSTEM}
    msgs = [system] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("role") != "system"]
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        max_tokens=1024,
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def _chat_gemini(api_key: str, model: str, messages: List[dict]) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    system = {"role": "system", "content": COPILOT_SYSTEM}
    msgs = [system] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("role") != "system"]
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        max_tokens=1024,
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def _chat_anthropic(api_key: str, model: str, messages: List[dict]) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    conv = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("role") != "system"]
    if not conv or conv[-1].get("role") != "user":
        raise ValueError("Last message must be from user")
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.7,
        system=COPILOT_SYSTEM,
        messages=conv,
    )
    if resp.content and len(resp.content) > 0:
        return (resp.content[0].text or "").strip()
    return ""
