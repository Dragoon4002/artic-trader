"""Background price feed: poll Pyth every N seconds, cache in-memory, broadcast via WS."""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .pyth_proxy import fetch_prices_batch

logger = logging.getLogger(__name__)

# In-memory price cache — module-level singleton
# { "BTCUSDT": {"symbol": "BTCUSDT", "price": 72160.0, "fetched_at": "..."} }
price_cache: dict[str, dict] = {}

# Extra symbols to track beyond active agents (e.g. default watchlist)
_extra_symbols: set[str] = set()


def track_symbol(symbol: str) -> None:
    _extra_symbols.add(symbol.upper())


def get_price(symbol: str) -> dict | None:
    return price_cache.get(symbol.upper())


def get_all_prices() -> dict[str, dict]:
    return dict(price_cache)


async def _get_active_symbols(session_factory) -> list[str]:
    """Deduplicated symbols for all alive agents."""
    from ..db.models.agent import Agent
    async with session_factory() as db:
        result = await db.execute(
            select(Agent.symbol).where(Agent.status == "alive")
        )
        return list({row[0] for row in result.all()})


async def price_feed_loop(session_factory, broadcast_prices_fn, poll_seconds: float = 2.0):
    """Background task — runs forever, never raises."""
    logger.info("[PriceFeed] Starting bulk price feed loop")

    while True:
        try:
            agent_symbols = await _get_active_symbols(session_factory)
            all_symbols = list(set(agent_symbols) | _extra_symbols)

            if all_symbols:
                prices = await fetch_prices_batch(all_symbols)
                price_cache.update(prices)

                if broadcast_prices_fn and prices:
                    await broadcast_prices_fn(price_cache)
        except Exception as e:
            logger.error(f"[PriceFeed] Error: {e}")

        await asyncio.sleep(poll_seconds)
