"""Centralized candle cache with APScheduler refresh."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..config import settings
from ..db.base import get_session, async_session
from ..db.models.market_cache import MarketCache

router = APIRouter(prefix="/api/market", tags=["market"])

# Tracked symbols for background refresh
_tracked_symbols: set[tuple[str, str]] = set()


@router.get("/candles")
async def get_candles(
    symbol: str = Query(...),
    interval: str = Query("15m"),
    db: AsyncSession = Depends(get_session),
):
    """Serve cached candles or fetch fresh from TwelveData."""
    _tracked_symbols.add((symbol, interval))

    # Check cache
    result = await db.execute(
        select(MarketCache).where(
            MarketCache.symbol == symbol, MarketCache.timeframe == interval
        )
    )
    cached = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if cached and (now - cached.last_fetched.replace(tzinfo=timezone.utc)).total_seconds() < settings.CANDLE_STALENESS_SECONDS:
        return {"symbol": symbol, "interval": interval, "candles": cached.candles, "cached": True}

    # Fetch fresh
    candles = await _fetch_from_twelvedata(symbol, interval)
    if candles is None:
        if cached:
            return {"symbol": symbol, "interval": interval, "candles": cached.candles, "cached": True, "stale": True}
        return {"symbol": symbol, "interval": interval, "candles": [], "error": "fetch failed"}

    if cached:
        cached.candles = candles
        cached.last_fetched = now
    else:
        cached = MarketCache(symbol=symbol, timeframe=interval, candles=candles, last_fetched=now)
        db.add(cached)
    await db.commit()

    return {"symbol": symbol, "interval": interval, "candles": candles, "cached": False}


async def _fetch_from_twelvedata(symbol: str, interval: str) -> list | None:
    """Fetch candles from TwelveData API."""
    if not settings.TWELVE_DATA_API_KEY:
        return None
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 100,
        "apikey": settings.TWELVE_DATA_API_KEY,
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=15)
            data = r.json()
        if data.get("status") == "error":
            return None
        values = data.get("values", [])
        return [
            {
                "datetime": v.get("datetime"),
                "open": float(v.get("open", 0)),
                "high": float(v.get("high", 0)),
                "low": float(v.get("low", 0)),
                "close": float(v.get("close", 0)),
                "volume": float(v.get("volume", 0)),
            }
            for v in values
        ]
    except Exception:
        return None


async def refresh_all_tracked():
    """Background job: refresh all tracked symbol/interval pairs."""
    async with async_session() as db:
        for symbol, interval in list(_tracked_symbols):
            candles = await _fetch_from_twelvedata(symbol, interval)
            if candles is None:
                continue
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(MarketCache).where(
                    MarketCache.symbol == symbol, MarketCache.timeframe == interval
                )
            )
            cached = result.scalar_one_or_none()
            if cached:
                cached.candles = candles
                cached.last_fetched = now
            else:
                db.add(MarketCache(symbol=symbol, timeframe=interval, candles=candles, last_fetched=now))
            await db.commit()
