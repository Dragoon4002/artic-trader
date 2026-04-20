"""TwelveData REST client — candle fetches.

Free-tier rate limit: 8 req/min/key. `scheduler.py` enforces pacing across jobs.
"""

from __future__ import annotations

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.twelvedata.com/time_series"


async def fetch_candles(
    symbol: str, interval: str, size: int = 100
) -> list[dict] | None:
    """Return list of OHLCV dicts newest-first, or None on failure."""
    if not settings.TWELVE_DATA_API_KEY:
        return None
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": size,
        "apikey": settings.TWELVE_DATA_API_KEY,
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(_BASE_URL, params=params)
            data = r.json()
    except Exception as e:
        logger.warning("twelvedata fetch error %s/%s: %s", symbol, interval, e)
        return None
    if data.get("status") == "error":
        logger.warning(
            "twelvedata error %s/%s: %s", symbol, interval, data.get("message")
        )
        return None
    return [
        {
            "datetime": v.get("datetime"),
            "open": float(v.get("open", 0)),
            "high": float(v.get("high", 0)),
            "low": float(v.get("low", 0)),
            "close": float(v.get("close", 0)),
            "volume": float(v.get("volume", 0)),
        }
        for v in data.get("values", [])
    ]
