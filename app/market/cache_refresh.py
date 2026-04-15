"""
Background refresh: fetch from CMC, Twelve Data, Pyth and upsert into MongoDB.
Designed to run every 1 minute (token_detail + pyth); historical can run every 1 min for short ranges.
"""
import os
import time
from datetime import datetime, timezone
from typing import List

import requests

from .db import (
    get_db,
    token_detail_collection,
    token_historical_collection,
    pyth_prices_collection,
    normalize_symbol,
)


# Default symbols to cache when TRACKED_SYMBOLS is not set
DEFAULT_TRACKED_SYMBOLS = ["BTC", "ETH", "BNB", "SOL"]
# Ranges to cache for historical chart
HISTORICAL_RANGES = ["24h", "7d", "1m", "3m", "1y"]
from .pyth_client import PYTH_FEED_IDS as _RAW_FEED_IDS, HERMES_URL
# Re-key to "SYM/USD" format for backward compat with refresh_pyth_prices
PYTH_FEED_IDS = {f"{sym}/USD": fid for sym, fid in _RAW_FEED_IDS.items()}


def _tracked_symbols() -> List[str]:
    raw = (os.getenv("TRACKED_SYMBOLS") or "").strip()
    if not raw:
        return DEFAULT_TRACKED_SYMBOLS
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Read-through helpers: call these when you fetch from API so cache is populated ----------


def upsert_token_detail(detail: dict) -> None:
    """Write a single token detail (from CMC) into MongoDB. No-op if MongoDB not configured."""
    coll = token_detail_collection()
    if coll is None or not detail:
        return
    sym = detail.get("symbol")
    if not sym:
        return
    doc = {**detail, "symbol": sym, "updated_at": _now_iso()}
    try:
        coll.update_one({"symbol": sym}, {"$set": doc}, upsert=True)
    except Exception as e:
        print(f"[CacheRefresh] upsert_token_detail {sym}: {e}")


def upsert_token_details(details: list) -> None:
    """Write multiple token details into MongoDB. No-op if MongoDB not configured."""
    coll = token_detail_collection()
    if coll is None or not details:
        return
    updated = _now_iso()
    for detail in details:
        sym = detail.get("symbol")
        if not sym:
            continue
        try:
            doc = {**detail, "symbol": sym, "updated_at": updated}
            coll.update_one({"symbol": sym}, {"$set": doc}, upsert=True)
        except Exception as e:
            print(f"[CacheRefresh] upsert_token_details {sym}: {e}")


def upsert_token_historical(symbol: str, range_key: str, result: dict) -> None:
    """Write historical chart result into MongoDB. No-op if MongoDB not configured."""
    coll = token_historical_collection()
    if coll is None or not result:
        return
    sym = normalize_symbol(symbol)
    range_key = (range_key or "1y").strip().lower()
    doc = {
        "symbol": sym,
        "range": result.get("range", range_key),
        "data": result.get("data", []),
        "updated_at": _now_iso(),
    }
    try:
        coll.update_one(
            {"symbol": sym, "range": range_key},
            {"$set": doc},
            upsert=True,
        )
    except Exception as e:
        print(f"[CacheRefresh] upsert_token_historical {sym} {range_key}: {e}")


def refresh_token_detail() -> None:
    """Fetch token details from CMC (batch) and upsert into token_detail."""
    coll = token_detail_collection()
    if coll is None:
        return
    cmc_key = os.getenv("CMC_API_KEY")
    if not cmc_key:
        return
    symbols = _tracked_symbols()
    try:
        from .cmc_client import CMCClient
        client = CMCClient(api_key=cmc_key)
        data = client.get_tokens_batch(symbols, convert="USD")
    except Exception as e:
        print(f"[CacheRefresh] CMC batch failed: {e}")
        return
    updated = _now_iso()
    for detail in data:
        sym = detail.get("symbol")
        if not sym:
            continue
        doc = {**detail, "symbol": sym, "updated_at": updated}
        coll.update_one(
            {"symbol": sym},
            {"$set": doc},
            upsert=True,
        )
    print(f"[CacheRefresh] token_detail: upserted {len(data)} symbols")


def refresh_token_historical() -> None:
    """Fetch historical chart data from Twelve Data and upsert into token_historical."""
    coll = token_historical_collection()
    if coll is None:
        return
    twelve_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_key:
        return
    try:
        from .market import MarketData
        from .token_analysis import get_historical_chart_data
        market_data = MarketData(twelve_data_api_key=twelve_key)
    except Exception as e:
        print(f"[CacheRefresh] MarketData init failed: {e}")
        return
    updated = _now_iso()
    for symbol in _tracked_symbols():
        for range_key in HISTORICAL_RANGES:
            try:
                result = get_historical_chart_data(symbol, range_key, market_data)
                doc = {
                    "symbol": symbol,
                    "range": result.get("range", range_key),
                    "data": result.get("data", []),
                    "updated_at": updated,
                }
                coll.update_one(
                    {"symbol": symbol, "range": range_key},
                    {"$set": doc},
                    upsert=True,
                )
            except Exception as e:
                print(f"[CacheRefresh] historical {symbol} {range_key}: {e}")
            time.sleep(8)  # Twelve Data free tier: 8 calls/min — space out requests
    print(f"[CacheRefresh] token_historical: refreshed {len(_tracked_symbols())} symbols x {len(HISTORICAL_RANGES)} ranges")


def refresh_pyth_prices() -> None:
    """Fetch Pyth prices from Hermes and upsert into pyth_prices."""
    coll = pyth_prices_collection()
    if coll is None:
        return
    ids = list(PYTH_FEED_IDS.values())
    params = "&".join(f"ids[]={id}" for id in ids)
    try:
        r = requests.get(f"{HERMES_URL}/v2/updates/price/latest?{params}", timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[CacheRefresh] Pyth Hermes failed: {e}")
        return
    id_to_pair = {v.lower(): k for k, v in PYTH_FEED_IDS.items()}
    parsed = data.get("parsed") or []
    updated = _now_iso()
    for p in parsed:
        pair = id_to_pair.get(p.get("id", "").lower())
        if not pair:
            continue
        price_info = p.get("price") or {}
        expo = price_info.get("expo", 0)
        price = float(price_info.get("price", 0)) * (10 ** expo)
        conf = float(price_info.get("conf", 0)) * (10 ** expo)
        publish_time = price_info.get("publish_time", 0)
        doc = {
            "pair": pair,
            "price": price,
            "conf": conf,
            "publishTime": publish_time,
            "updated_at": updated,
        }
        coll.update_one(
            {"pair": pair},
            {"$set": doc},
            upsert=True,
        )
    print(f"[CacheRefresh] pyth_prices: upserted {len(parsed)} pairs")


def run_refresh() -> None:
    """Run all cache refreshes. Safe to call from scheduler or on startup."""
    if get_db() is None:
        return
    from datetime import datetime
    print(f"[CacheRefresh] run started at {datetime.now().strftime('%H:%M:%S')} (scheduled every 60s)")
    refresh_token_detail()
    refresh_token_historical()
    refresh_pyth_prices()


def run_refresh_quotes() -> None:
    """Refresh token_detail + pyth only (fast, for 60s interval). No Twelve Data historical."""
    if get_db() is None:
        return
    refresh_token_detail()
    refresh_pyth_prices()


def run_refresh_historical() -> None:
    """Refresh token_historical only (Twelve Data; runs every 5 min to respect rate limit)."""
    if get_db() is None:
        return
    from datetime import datetime
    print(f"[CacheRefresh] historical run at {datetime.now().strftime('%H:%M:%S')} (every 5 min)")
    refresh_token_historical()
