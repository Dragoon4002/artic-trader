"""
Token analysis for detail/audit pages: LLM-generated intro + social sentiment, hardcoded scores, historical chart data.
Uses OpenAI for narrative/sentiment and Twelve Data for historical price series.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI


# ---------- Hardcoded scores (placeholder until real scoring) ----------
def get_placeholder_scores(symbol: str) -> Dict[str, Any]:
    """Return Financial, Fundamental, Social, Security scores. Same shape for all tokens for now."""
    # Optional: vary slightly by symbol for demo (e.g. BTC vs small cap)
    symbol_upper = (symbol or "").strip().upper()
    if symbol_upper in ("BTC", "BITCOIN"):
        return {"financial": 93, "fundamental": 88, "social": 90, "security": 83}
    if symbol_upper in ("ETH", "ETHEREUM"):
        return {"financial": 90, "fundamental": 90, "social": 88, "security": 85}
    if symbol_upper in ("SOL", "SOLANA"):
        return {"financial": 85, "fundamental": 82, "social": 84, "security": 80}
    # Default
    return {"financial": 80, "fundamental": 78, "social": 75, "security": 82}


# ---------- OpenAI: detailed intro ----------
def _get_openai_client() -> OpenAI:
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY not set. Required for token analysis.")
    return OpenAI(api_key=key)


def generate_token_intro(
    name: str,
    symbol: str,
    description: Optional[str] = None,
    urls: Optional[Dict[str, List[str]]] = None,
    price: Optional[float] = None,
    circulating_supply: Optional[float] = None,
    max_supply: Optional[float] = None,
    date_added: Optional[str] = None,
    percent_change_24h: Optional[float] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate an audit-style introduction that includes key CMC-style data (supply, launch, price context).
    Returns one medium paragraph (4-6 sentences) suitable for the token header.
    """
    client = _get_openai_client()
    context = description or f"{name} ({symbol}) is a cryptocurrency."
    if urls:
        links = []
        for k, v in (urls or {}).items():
            if isinstance(v, list) and v:
                links.append(f"{k}: {v[0]}")
            elif isinstance(v, str):
                links.append(f"{k}: {v}")
        if links:
            context += "\nRelevant links: " + "; ".join(links[:5])

    # Build CMC data line for the prompt so the intro can include it
    cmc_facts = []
    if date_added:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_added.replace("Z", "+00:00"))
            cmc_facts.append(f"Launched/listed: {dt.year}")
        except Exception:
            cmc_facts.append(f"Date added: {date_added[:10]}" if len(date_added or "") >= 10 else date_added or "")
    if circulating_supply is not None and circulating_supply > 0:
        if circulating_supply >= 1e9:
            cmc_facts.append(f"Current supply: {circulating_supply / 1e9:.2f}B {symbol}")
        elif circulating_supply >= 1e6:
            cmc_facts.append(f"Current supply: {circulating_supply / 1e6:.2f}M {symbol}")
        else:
            cmc_facts.append(f"Current supply: {circulating_supply:,.0f} {symbol}")
    if max_supply is not None and max_supply > 0:
        if max_supply >= 1e9:
            cmc_facts.append(f"Max supply: {max_supply / 1e9:.2f}B")
        elif max_supply >= 1e6:
            cmc_facts.append(f"Max supply: {max_supply / 1e6:.2f}M")
        else:
            cmc_facts.append(f"Max supply: {max_supply:,.0f}")
    if price is not None:
        cmc_facts.append(f"Current price: ${price:,.2f}" if price >= 1 else f"Current price: ${price:.6f}")
    if percent_change_24h is not None:
        cmc_facts.append(f"24h change: {percent_change_24h:+.2f}%")
    if cmc_facts:
        context += "\nData from CMC: " + "; ".join(cmc_facts)

    system = (
        "You are a professional crypto analyst. Write in a neutral, informative tone. "
        "Output only the introduction text, no JSON or labels. Weave in the CMC data naturally."
    )
    user = (
        f"Write one medium-length paragraph (4-6 sentences) for {name} ({symbol}). "
        f"Context:\n\n{context}\n\n"
        "Include: what the project is, when it launched (if given), current supply and max supply (if given), "
        "and current trading context (price and 24h change if given). Use the exact numbers from the CMC data. "
        "Keep it readable and suitable for a token audit card."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=450,
        temperature=0.5,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text if text else (description or f"{name} ({symbol}) – no introduction generated.")


# ---------- OpenAI: financial analysis (for section 2) ----------
def generate_financial_analysis(
    name: str,
    symbol: str,
    price: Optional[float] = None,
    market_cap: Optional[float] = None,
    volume_24h: Optional[float] = None,
    percent_change_24h: Optional[float] = None,
    percent_change_7d: Optional[float] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate a short financial analysis of the current market for the token (for section 2).
    """
    client = _get_openai_client()
    parts = [f"Token: {name} ({symbol})."]
    if price is not None:
        parts.append(f"Current price: ${price:,.2f}" if price >= 1 else f"Current price: ${price:.6f}")
    if market_cap is not None and market_cap >= 1e9:
        parts.append(f"Market cap: ${market_cap / 1e9:.2f}B")
    if volume_24h is not None and volume_24h >= 1e6:
        parts.append(f"24h volume: ${volume_24h / 1e9:.2f}B")
    if percent_change_24h is not None:
        parts.append(f"24h change: {percent_change_24h:+.2f}%")
    if percent_change_7d is not None:
        parts.append(f"7d change: {percent_change_7d:+.2f}%")
    context = " ".join(parts)

    system = "You are a crypto market analyst. Write one short paragraph only. No bullet points or JSON."
    user = (
        f"{context}\n\n"
        "Write a brief financial analysis of the current market for this token: "
        "outlook, key levels, or sentiment in 2-4 sentences. Be concise."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=250,
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text if text else "Financial analysis unavailable."
    except Exception:
        return "Financial analysis unavailable."


# ---------- OpenAI: social sentiment (JSON) ----------
SOCIAL_JSON_SCHEMA = """
You must respond with a single JSON object (no markdown, no code block) with this exact structure:
{
  "community_sentiment": "good",
  "community_sentiment_score": 75,
  "community_summary": "One sentence summary of overall community sentiment.",
  "market_sentiment_summary": "One short paragraph summarizing market sentiment from X (Twitter), Reddit, CoinGecko and other sources. What is the overall mood and key themes?",
  "platforms": [
    {
      "name": "Twitter",
      "status": "GOOD",
      "url": "https://x.com/...",
      "sentiment": "One short sentence on sentiment from X/Twitter for this token.",
      "metrics": { "posts": 29971, "posts_change": 2, "users": 8462563, "users_change": 2786 }
    },
    {
      "name": "Reddit",
      "status": "GOOD",
      "url": "https://reddit.com/r/...",
      "sentiment": "One short sentence on Reddit sentiment.",
      "metrics": { "subscribers": 8036005, "active_users": 0 }
    },
    {
      "name": "CoinGecko",
      "status": "GOOD",
      "url": "https://coingecko.com/...",
      "sentiment": "One short sentence on watchlist/interest from CoinGecko.",
      "metrics": { "users_watching": 2354111, "users_watching_change": 458 }
    }
  ]
}
- community_sentiment: one of "good", "neutral", "bad"
- community_sentiment_score: number 0-100
- market_sentiment_summary: one paragraph on overall market sentiment from social/sources
- status per platform: one of "GOOD", "NEUTRAL", "BAD"
- sentiment per platform: one short sentence for that source
- metrics: plausible numbers; at least one per platform.
"""


def generate_social_sentiment(
    name: str,
    symbol: str,
    urls: Optional[Dict[str, List[str]]] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Generate social sentiment and per-platform summary using OpenAI.
    Returns dict: community_sentiment, community_sentiment_score, community_summary, platforms.
    """
    client = _get_openai_client()
    url_hints = []
    if urls:
        for k, v in (urls or {}).items():
            if isinstance(v, list) and v and v[0]:
                url_hints.append(f"{k}: {v[0]}")
            elif isinstance(v, str) and v:
                url_hints.append(f"{k}: {v}")
    context = f"Token: {name} ({symbol}). " + ("; ".join(url_hints) if url_hints else "No URLs provided.")

    system = (
        "You are a crypto community analyst. You output only valid JSON with the exact keys requested. "
        "Do not wrap in markdown or code blocks."
    )
    user = (
        f"Based on typical community presence for {name} ({symbol}), generate social sentiment data.\n"
        f"Context: {context}\n\n"
        + SOCIAL_JSON_SCHEMA
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        max_tokens=1024,
        temperature=0.4,
    )
    raw = (resp.choices[0].message.content or "").strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _default_social(name, symbol, urls)
    # Normalize to expected shape
    platforms = data.get("platforms") or []
    for p in platforms:
        if isinstance(p, dict):
            p.setdefault("status", "NEUTRAL")
            p.setdefault("metrics", {})
            p.setdefault("sentiment", "")
    return {
        "community_sentiment": data.get("community_sentiment") or "neutral",
        "community_sentiment_score": _int_in_range(data.get("community_sentiment_score"), 0, 100, 50),
        "community_summary": data.get("community_summary") or "Community sentiment data not available.",
        "market_sentiment_summary": data.get("market_sentiment_summary") or "",
        "platforms": platforms[:10],
    }


def _int_in_range(val: Any, lo: int, hi: int, default: int) -> int:
    try:
        n = int(val)
        return max(lo, min(hi, n))
    except (TypeError, ValueError):
        return default


def _default_social(name: str, symbol: str, urls: Optional[Dict] = None) -> Dict[str, Any]:
    """Fallback when LLM response is invalid."""
    platforms = []
    if urls:
        if urls.get("website"):
            platforms.append({"name": "Website", "status": "NEUTRAL", "url": (urls["website"] or [""])[0], "metrics": {}})
        if urls.get("reddit"):
            platforms.append({"name": "Reddit", "status": "NEUTRAL", "url": (urls["reddit"] or [""])[0], "metrics": {"subscribers": 0}})
        if urls.get("twitter"):
            platforms.append({"name": "Twitter", "status": "NEUTRAL", "url": (urls["twitter"] or [""])[0], "metrics": {"posts": 0, "users": 0}})
    if not platforms:
        platforms = [
            {"name": "Twitter", "status": "NEUTRAL", "url": "", "metrics": {}},
            {"name": "Reddit", "status": "NEUTRAL", "url": "", "metrics": {}},
            {"name": "CoinGecko", "status": "NEUTRAL", "url": "", "metrics": {}},
        ]
    return {
        "community_sentiment": "neutral",
        "community_sentiment_score": 50,
        "community_summary": f"Community data for {name} ({symbol}) is not yet available.",
        "market_sentiment_summary": "",
        "platforms": platforms,
    }


# ---------- Historical chart data (Twelve Data) ----------
# Range -> (interval for Twelve Data, number of points or days)
RANGE_CONFIG = {
    "24h": ("1h", 24),       # 24 hourly bars
    "7d": ("4h", 42),        # 7*6 = 42 bars of 4h
    "1m": ("1day", 30),
    "3m": ("1day", 90),
    "1y": ("1day", 365),
    "max": ("1day", 5000),
}


def get_historical_chart_data(
    symbol: str,
    range_key: str,
    market_data: Any,
) -> Dict[str, Any]:
    """
    Fetch historical price series for the Financial Audit chart.
    range_key: one of 24h, 7d, 1m, 3m, 1y, max.
    market_data: MarketData instance (from app.market) with get_ohlcv_candles and get_historical_data.
    Returns { "range": range_key, "data": [ { "date", "timestamp", "price", "open", "high", "low", "volume" }, ... ] }.
    """
    range_key = (range_key or "1y").strip().lower()
    if range_key not in RANGE_CONFIG:
        range_key = "1y"
    interval, size = RANGE_CONFIG[range_key]

    if interval == "1day":
        # Use daily historical (returns list of dicts)
        days = min(size, 5000)
        raw = market_data.get_historical_data(symbol, days=days) or []
    else:
        # Use OHLCV candles (1h or 4h)
        tf = "1h" if interval == "1h" else "4h"
        raw_candles = market_data.get_ohlcv_candles(symbol, tf, size)
        if not raw_candles:
            return {"range": range_key, "data": []}
        raw = [
            {
                "date": c.timestamp.isoformat(),
                "timestamp": int(c.timestamp.timestamp() * 1000),
                "price": c.close,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "volume": c.volume,
            }
            for c in raw_candles
        ]

    if not raw:
        return {"range": range_key, "data": []}
    # Normalize: ensure each point has date, timestamp, price, open, high, low, volume
    data = []
    for v in raw:
        if isinstance(v, dict):
            data.append({
                "date": v.get("date"),
                "timestamp": v.get("timestamp"),
                "price": v.get("price"),
                "open": v.get("open"),
                "high": v.get("high"),
                "low": v.get("low"),
                "volume": v.get("volume") or v.get("volume_24h"),
            })
        else:
            data.append({
                "date": getattr(v, "date", None),
                "timestamp": getattr(v, "timestamp", None),
                "price": getattr(v, "price", None),
                "open": getattr(v, "open", None),
                "high": getattr(v, "high", None),
                "low": getattr(v, "low", None),
                "volume": getattr(v, "volume", None) or getattr(v, "volume_24h", None),
            })
    return {"range": range_key, "data": data}


# ---------- Full analysis payload (no historical; use GET /token/{symbol}/historical separately) ----------
def build_token_analysis(
    token_detail: Dict[str, Any],
    include_intro: bool = True,
    include_social: bool = True,
    openai_model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Build the token analysis response: intro (LLM), scores (hardcoded), social (LLM), token (CMC summary).
    Historical chart data is not included; use GET /token/{symbol}/historical?range=... separately.
    token_detail: from CMCClient.get_token_detail().
    """
    name = token_detail.get("name") or token_detail.get("symbol") or "Unknown"
    symbol = token_detail.get("symbol") or ""

    scores = get_placeholder_scores(symbol)

    intro = ""
    if include_intro:
        try:
            intro = generate_token_intro(
                name=name,
                symbol=symbol,
                description=token_detail.get("description"),
                urls=token_detail.get("urls"),
                price=token_detail.get("price"),
                circulating_supply=token_detail.get("circulating_supply"),
                max_supply=token_detail.get("max_supply"),
                date_added=token_detail.get("date_added"),
                percent_change_24h=token_detail.get("percent_change_24h"),
                model=openai_model,
            )
        except Exception as e:
            intro = token_detail.get("description") or f"{name} ({symbol}) – intro unavailable ({e})."

    financial_analysis = ""
    try:
        financial_analysis = generate_financial_analysis(
            name=name,
            symbol=symbol,
            price=token_detail.get("price"),
            market_cap=token_detail.get("market_cap"),
            volume_24h=token_detail.get("volume_24h"),
            percent_change_24h=token_detail.get("percent_change_24h"),
            percent_change_7d=token_detail.get("percent_change_7d"),
            model=openai_model,
        )
    except Exception:
        financial_analysis = ""

    social = {}
    if include_social:
        try:
            social = generate_social_sentiment(
                name=name,
                symbol=symbol,
                urls=token_detail.get("urls"),
                model=openai_model,
            )
        except Exception as e:
            social = _default_social(name, symbol, token_detail.get("urls"))
            social["community_summary"] = f"Sentiment unavailable ({e})."

    # Minimal token summary for this response (full CMC data is from GET /token/{symbol})
    token_summary = {
        "symbol": token_detail.get("symbol"),
        "name": token_detail.get("name"),
        "slug": token_detail.get("slug"),
        "price": token_detail.get("price"),
        "percent_change_24h": token_detail.get("percent_change_24h"),
        "market_cap": token_detail.get("market_cap"),
        "volume_24h": token_detail.get("volume_24h"),
        "volume_change_24h": token_detail.get("volume_change_24h"),
        "logo": token_detail.get("logo"),
    }

    return {
        "intro": intro,
        "scores": scores,
        "financial_analysis": financial_analysis,
        "social": social,
        "token": token_summary,
    }
