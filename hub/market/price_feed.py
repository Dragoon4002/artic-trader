"""Background price feed: poll Pyth every N seconds, cache in-memory, broadcast via WS."""

import asyncio
import logging

from .pyth import fetch_prices_batch

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


async def price_feed_loop(broadcast_prices_fn, poll_seconds: float = 2.0):
    """Background task — runs forever, never raises.

    Source of symbols is the client-facing watchlist (`track_symbol`) plus whatever
    `/market/price/{symbol}` callers hit. Active-agent discovery moved to user-server.
    """
    logger.info("[PriceFeed] Starting bulk price feed loop")

    while True:
        try:
            symbols = list(_extra_symbols | set(price_cache.keys()))
            if symbols:
                prices = await fetch_prices_batch(symbols)
                price_cache.update(prices)
                if broadcast_prices_fn and prices:
                    await broadcast_prices_fn(price_cache)
        except Exception as e:
            logger.error(f"[PriceFeed] Error: {e}")

        await asyncio.sleep(poll_seconds)
