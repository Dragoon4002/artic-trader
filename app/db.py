"""
MongoDB helpers for optional API-response caching (CMC, Pyth, TwelveData).
Returns None when MONGODB_URI is unset — callers degrade to direct API calls.
"""

import os
import re

_client = None
_db = None


def get_db():
    """Return the MongoDB database instance, or None if MONGODB_URI is unset/invalid."""
    global _client, _db
    if _db is not None:
        return _db
    uri = (os.getenv("MONGODB_URI") or "").strip()
    if not uri or "xxxxx" in uri:
        return None
    try:
        from pymongo import MongoClient

        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client.get_default_database("arcgenesis")
        return _db
    except Exception as e:
        print(f"[db] MongoDB connection failed: {e}")
        return None


def ensure_indexes():
    """Create indexes on cached collections. No-op if MongoDB not connected."""
    db = get_db()
    if db is None:
        return
    db["token_detail"].create_index("symbol", unique=True)
    db["token_historical"].create_index([("symbol", 1), ("range", 1)], unique=True)
    db["pyth_prices"].create_index("pair", unique=True)


def token_detail_collection():
    db = get_db()
    return db["token_detail"] if db is not None else None


def token_historical_collection():
    db = get_db()
    return db["token_historical"] if db is not None else None


def pyth_prices_collection():
    db = get_db()
    return db["pyth_prices"] if db is not None else None


_STRIP_RE = re.compile(r"[-/]?(USD[TC]?|PERP|SWAP)$", re.IGNORECASE)


def normalize_symbol(symbol: str) -> str:
    """Normalize 'BTCUSDT', 'BTC/USD', 'BTC-PERP' → 'BTC'."""
    s = symbol.strip().upper()
    return _STRIP_RE.sub("", s) or s
