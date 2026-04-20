"""Candle cache — DB-backed, stale-after N seconds."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import base as db_base
from ..db.models.market_cache import MarketCache
from . import twelvedata

# Tracked symbols for background refresh; updated on every /market/candles hit.
tracked: set[tuple[str, str]] = set()


async def get_or_fetch(db: AsyncSession, symbol: str, interval: str) -> dict:
    """Serve cached candles or re-fetch from TwelveData."""
    tracked.add((symbol, interval))
    cached = (
        await db.execute(
            select(MarketCache).where(
                MarketCache.symbol == symbol, MarketCache.timeframe == interval
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if cached and _fresh(cached.last_fetched, now):
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": cached.candles,
            "cached": True,
        }

    fresh = await twelvedata.fetch_candles(symbol, interval)
    if fresh is None:
        if cached:
            return {
                "symbol": symbol,
                "interval": interval,
                "candles": cached.candles,
                "cached": True,
                "stale": True,
            }
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": [],
            "error": "fetch failed",
        }

    if cached:
        cached.candles = fresh
        cached.last_fetched = now
    else:
        db.add(
            MarketCache(
                symbol=symbol, timeframe=interval, candles=fresh, last_fetched=now
            )
        )
    await db.commit()
    return {"symbol": symbol, "interval": interval, "candles": fresh, "cached": False}


async def refresh_all_tracked() -> None:
    """APScheduler-driven: refresh every tracked (symbol, interval) pair."""
    async with db_base.async_session() as db:
        for symbol, interval in list(tracked):
            fresh = await twelvedata.fetch_candles(symbol, interval)
            if fresh is None:
                continue
            now = datetime.now(timezone.utc)
            row = (
                await db.execute(
                    select(MarketCache).where(
                        MarketCache.symbol == symbol, MarketCache.timeframe == interval
                    )
                )
            ).scalar_one_or_none()
            if row:
                row.candles = fresh
                row.last_fetched = now
            else:
                db.add(
                    MarketCache(
                        symbol=symbol,
                        timeframe=interval,
                        candles=fresh,
                        last_fetched=now,
                    )
                )
            await db.commit()


def _fresh(last_fetched: datetime, now: datetime) -> bool:
    age = (now - last_fetched.replace(tzinfo=timezone.utc)).total_seconds()
    return age < settings.CANDLE_STALENESS_SECONDS
