"""Market endpoints — live prices (Pyth) + cached candles (TwelveData)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from . import cache
from .price_feed import get_all_prices, get_price
from .pyth import fetch_prices_batch

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/price/{symbol}")
async def price_one(symbol: str):
    symbol = symbol.upper()
    cached = get_price(symbol)
    if cached:
        return cached
    prices = await fetch_prices_batch([symbol])
    if symbol in prices:
        return prices[symbol]
    raise HTTPException(status_code=404, detail=f"no price feed for {symbol}")


@router.get("/prices")
async def price_all():
    return get_all_prices()


@router.get("/candles")
async def candles(
    symbol: str = Query(...),
    interval: str = Query("15m"),
    db: AsyncSession = Depends(get_session),
):
    return await cache.get_or_fetch(db, symbol, interval)
