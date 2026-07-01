"""
Concurrent historical chart data fetcher for cache_refresh.
Uses ThreadPoolExecutor to parallelize Twelve Data API calls
while respecting rate limits (8s between calls on free tier).
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from .market import MarketData


def fetch_historical_parallel(symbols, ranges, market_data, max_workers=4, rate_limit_delay=8.0):
    """Fetch historical chart data for multiple symbols and ranges in parallel."""
    results = []

    def fetch_one(symbol, range_key):
        try:
            from .token_analysis import get_historical_chart_data
            result = get_historical_chart_data(symbol, range_key, market_data)
            return {"symbol": symbol, "range": result.get("range", range_key), "data": result.get("data", [])}
        except Exception as e:
            print(f"[CacheRefreshParallel] historical {symbol} {range_key}: {e}")
            return None

    tasks = [(symbol, rk) for symbol in symbols for rk in ranges]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(fetch_one, symbol, range_key): (symbol, range_key)
            for symbol, range_key in tasks
        }
        for future in as_completed(future_to_task):
            result = future.result()
            if result is not None:
                results.append(result)
            time.sleep(rate_limit_delay / max(len(symbols), 1))

    return results
