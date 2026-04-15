"""
CoinMarketCap API client for detailed token data.
Fetches live quotes + metadata for use in token detail pages and indexing.
"""
import os
import time
from typing import Any, Dict, List, Optional

import requests


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol for API (e.g. BTCUSDT -> BTC, BINANCE:ETHUSDT -> ETH)."""
    s = (symbol or "").strip().upper()
    if ":" in s:
        s = s.split(":")[-1]
    for suffix in ["USDT", "USD", "BUSD", "USDC", "PERP"]:
        if s.endswith(f"-{suffix}") or s.endswith(suffix):
            s = s.replace(f"-{suffix}", "").replace(suffix, "")
            break
    return s or symbol


class CMCClient:
    """
    Fetches detailed token data from CoinMarketCap:
    - Latest quotes (price, volume, market_cap, % changes)
    - Metadata (description, logo, urls, contract addresses)
    """

    BASE_URL = "https://pro-api.coinmarketcap.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        if not self.api_key:
            raise ValueError("CMC_API_KEY not set")
        self.headers = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json",
        }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Optional[Dict]:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        try:
            r = requests.get(url, headers=self.headers, params=params or {}, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"[CMC] Request failed {path}: {e}")
            return None
        except ValueError as e:
            print(f"[CMC] JSON decode failed {path}: {e}")
            return None

    def get_token_detail(self, symbol: str, convert: str = "USD") -> Optional[Dict[str, Any]]:
        """
        Fetch all available live data for one token from CMC: quotes + metadata.
        Symbol can be: BTC, ETH, BTCUSDT, BTC-PERP, etc.

        Returns a single merged object suitable for token detail pages and indexing.
        """
        cmc_symbol = _normalize_symbol(symbol)
        if not cmc_symbol:
            return None

        # 1) Latest quotes (includes id, name, symbol, slug, quote.USD)
        quote_data = self._get(
            "cryptocurrency/quotes/latest",
            params={"symbol": cmc_symbol, "convert": convert},
        )
        if not quote_data or "data" not in quote_data or cmc_symbol not in quote_data["data"]:
            return None

        raw = quote_data["data"][cmc_symbol]
        token_id = raw.get("id")
        quote_usd = (raw.get("quote") or {}).get(convert) or {}

        def num(k: str, default: Optional[float] = None):
            v = quote_usd.get(k)
            if v is None:
                return default
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        detail: Dict[str, Any] = {
            "symbol": raw.get("symbol"),
            "name": raw.get("name"),
            "slug": raw.get("slug"),
            "cmc_id": token_id,
            "price": num("price"),
            "volume_24h": num("volume_24h"),
            "volume_change_24h": num("volume_change_24h"),
            "market_cap": num("market_cap"),
            "market_cap_dominance": num("market_cap_dominance"),
            "percent_change_1h": num("percent_change_1h"),
            "percent_change_24h": num("percent_change_24h"),
            "percent_change_7d": num("percent_change_7d"),
            "percent_change_30d": num("percent_change_30d"),
            "fully_diluted_market_cap": num("fully_diluted_market_cap"),
            "last_updated_quote": quote_usd.get("last_updated"),
            "num_market_pairs": raw.get("num_market_pairs"),
            "circulating_supply": raw.get("circulating_supply"),
            "total_supply": raw.get("total_supply"),
            "max_supply": raw.get("max_supply"),
            "description": None,
            "logo": None,
            "urls": None,
            "date_added": None,
            "contract_address": None,
            "platform": None,
            "tags": None,
        }

        # 2) Metadata (description, logo, urls) – use id from quote
        if token_id:
            info_data = self._get("cryptocurrency/info", params={"id": token_id})
            if info_data and "data" in info_data and str(token_id) in info_data["data"]:
                info = info_data["data"][str(token_id)]
                detail["description"] = info.get("description")
                detail["logo"] = info.get("logo")
                detail["urls"] = info.get("urls")  # website, technical_doc, explorer, etc.
                detail["date_added"] = info.get("date_added")
                detail["tags"] = info.get("tags")
                # Platform/contract for tokens
                if info.get("platform"):
                    detail["platform"] = info["platform"].get("name")
                    detail["contract_address"] = info["platform"].get("token_address")

        return detail

    def get_token_detail_with_retry(
        self, symbol: str, convert: str = "USD", max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        for attempt in range(max_retries + 1):
            out = self.get_token_detail(symbol, convert=convert)
            if out is not None:
                return out
            if attempt < max_retries:
                time.sleep(0.3)
        return None

    def get_tokens_batch(
        self, symbols: List[str], convert: str = "USD"
    ) -> List[Dict[str, Any]]:
        """
        Fetch detail for multiple tokens. CMC allows multiple symbols in quotes/latest.
        Returns list of token detail dicts (skips missing).
        """
        if not symbols:
            return []
        cmc_symbols = [_normalize_symbol(s) for s in symbols]
        cmc_symbols = [s for s in cmc_symbols if s]
        if not cmc_symbols:
            return []
        # CMC accepts comma-separated symbols
        symbol_param = ",".join(cmc_symbols[:50])  # cap to avoid long URLs
        data = self._get(
            "cryptocurrency/quotes/latest",
            params={"symbol": symbol_param, "convert": convert},
        )
        if not data or "data" not in data:
            return []

        ids_to_fetch = []
        results = []
        for sym, raw in data["data"].items():
            token_id = raw.get("id")
            quote_usd = (raw.get("quote") or {}).get(convert) or {}

            def num(k: str, default: Optional[float] = None):
                v = quote_usd.get(k)
                if v is None:
                    return default
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return default

            detail = {
                "symbol": raw.get("symbol"),
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "cmc_id": token_id,
                "price": num("price"),
                "volume_24h": num("volume_24h"),
                "volume_change_24h": num("volume_change_24h"),
                "market_cap": num("market_cap"),
                "market_cap_dominance": num("market_cap_dominance"),
                "percent_change_1h": num("percent_change_1h"),
                "percent_change_24h": num("percent_change_24h"),
                "percent_change_7d": num("percent_change_7d"),
                "percent_change_30d": num("percent_change_30d"),
                "fully_diluted_market_cap": num("fully_diluted_market_cap"),
                "last_updated_quote": quote_usd.get("last_updated"),
                "num_market_pairs": raw.get("num_market_pairs"),
                "circulating_supply": raw.get("circulating_supply"),
                "total_supply": raw.get("total_supply"),
                "max_supply": raw.get("max_supply"),
                "description": None,
                "logo": None,
                "urls": None,
                "date_added": None,
                "contract_address": None,
                "platform": None,
                "tags": None,
            }
            if token_id:
                ids_to_fetch.append((token_id, detail))
            results.append(detail)

        # Optional: batch metadata (CMC info accepts multiple ids)
        if ids_to_fetch:
            id_param = ",".join(str(tid) for tid, _ in ids_to_fetch[:30])
            info_data = self._get("cryptocurrency/info", params={"id": id_param})
            if info_data and "data" in info_data:
                for token_id, detail in ids_to_fetch:
                    info = info_data["data"].get(str(token_id))
                    if not info:
                        continue
                    detail["description"] = info.get("description")
                    detail["logo"] = info.get("logo")
                    detail["urls"] = info.get("urls")
                    detail["date_added"] = info.get("date_added")
                    detail["tags"] = info.get("tags")
                    if info.get("platform"):
                        detail["platform"] = info["platform"].get("name")
                        detail["contract_address"] = info["platform"].get("token_address")

        return results
