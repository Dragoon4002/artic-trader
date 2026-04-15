"""REST endpoints for live price data."""
from fastapi import APIRouter, HTTPException

from .price_feed import price_cache, get_price, get_all_prices
from .pyth_proxy import fetch_prices_batch

router = APIRouter(prefix="/api/market", tags=["market-prices"])


@router.get("/price/{symbol}")
async def get_price_endpoint(symbol: str):
    symbol = symbol.upper()
    cached = get_price(symbol)
    if cached:
        return cached
    # Cache miss — direct fetch
    prices = await fetch_prices_batch([symbol])
    if symbol in prices:
        return prices[symbol]
    raise HTTPException(status_code=404, detail=f"No price feed for {symbol}")


@router.get("/prices")
async def get_all_prices_endpoint():
    return get_all_prices()
