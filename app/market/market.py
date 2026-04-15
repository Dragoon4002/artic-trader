"""
Market data fetching from Pyth Network (current prices) and Twelve Data API (historical OHLCV data).
When HUB_URL is set, candle fetches route through hub cache instead of calling TwelveData directly.
"""
import os
import requests
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from ..schemas import Candle
from .pyth_client import PythClient

_hub_url = os.getenv("HUB_URL")


def _normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol for API calls.
    Supports BINANCE:ETHUSDT, BINANCE:BTCUSDT (bnb-ai-trade format) -> ETHUSDT, BTCUSDT
    """
    s = symbol.strip().upper()
    if ":" in s:
        s = s.split(":")[-1]
    return s


class MarketData:
    """
    Fetches live market price from Pyth Network (Hermes REST)
    Fetches historical OHLCV data from Twelve Data API
    """

    TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"

    def __init__(self, api_key: Optional[str] = None, twelve_data_api_key: Optional[str] = None):
        self.twelve_data_api_key = twelve_data_api_key or os.getenv("TWELVE_DATA_API_KEY")
        if not self.twelve_data_api_key and not _hub_url:
            raise ValueError("TWELVE_DATA_API_KEY not set. Please set it in .env file or environment variables.")

        self.pyth = PythClient()
    
    def _symbol_to_twelvedata_symbol(self, symbol: str) -> str:
        """
        Convert trading symbol to Twelve Data format
        
        Args:
            symbol: Trading symbol like BTCUSDT, ETHUSDT, BINANCE:ETHUSDT
            
        Returns:
            Twelve Data symbol format (e.g., 'BTC/USD', 'ETH/USD')
        """
        symbol = _normalize_symbol(symbol)
        symbol_upper = symbol.upper()
        base_symbol = symbol_upper
        quote_currency = "USD"
        
        for suffix in ["USDT", "USD", "BUSD", "USDC"]:
            if symbol_upper.endswith(suffix):
                base_symbol = symbol_upper[:-len(suffix)]
                if suffix in ["USDT", "USD"]:
                    quote_currency = "USD"
                elif suffix == "BUSD":
                    quote_currency = "USD"
                elif suffix == "USDC":
                    quote_currency = "USD"
                break
        
        return f"{base_symbol}/{quote_currency}"
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Pyth Network."""
        return self.pyth.get_price(symbol)

    def get_price_with_retry(self, symbol: str, max_retries: int = 3) -> Optional[float]:
        """Fetch price from Pyth with retry logic."""
        return self.pyth.get_price_with_retry(symbol, max_retries=max_retries)
    
    def get_historical_data(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """
        Fetch historical price data from Twelve Data API
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'BINANCE:ETHUSDT')
            days: Number of days of historical data to fetch
            
        Returns:
            List of historical data points with date, price, etc., or None if fetch fails
        """
        try:
            # Convert symbol to Twelve Data format
            td_symbol = self._symbol_to_twelvedata_symbol(symbol)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Twelve Data time series endpoint
            url = f"{self.TWELVE_DATA_BASE_URL}/time_series"
            params = {
                "symbol": td_symbol,
                "interval": "1day",  # Daily data for historical
                "outputsize": min(days, 5000),  # Max 5000 records
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "apikey": self.twelve_data_api_key,
                "format": "JSON"
            }
            
            print(f"[INFO] Fetching historical data from Twelve Data for {symbol} ({td_symbol})...")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for errors in response
            if "status" in data and data["status"] == "error":
                error_msg = data.get("message", "Unknown error")
                print(f"[ERROR] Twelve Data API error: {error_msg}")
                return None
            
            # Twelve Data returns: { "values": [{"datetime": "...", "open": "...", "high": "...", "low": "...", "close": "...", "volume": "..."}, ...] }
            if "values" not in data:
                print(f"[WARN] No 'values' key in Twelve Data response for {symbol}")
                return None
            
            historical_data = []
            for value in data["values"]:
                try:
                    # Parse datetime
                    dt_str = value.get("datetime", "")
                    if dt_str:
                        dt = datetime.fromisoformat(dt_str.replace(" ", "T"))
                    else:
                        continue
                    
                    historical_data.append({
                        "date": dt.isoformat(),
                        "timestamp": int(dt.timestamp() * 1000),  # Milliseconds
                        "price": float(value.get("close", 0)),
                        "open": float(value.get("open", 0)),
                        "high": float(value.get("high", 0)),
                        "low": float(value.get("low", 0)),
                        "volume_24h": float(value.get("volume", 0)),
                        "market_cap": None,
                        "percent_change_24h": None,
                    })
                except (ValueError, KeyError) as e:
                    print(f"[WARN] Error parsing data point: {e}")
                    continue
            
            # Sort by timestamp (oldest first)
            historical_data.sort(key=lambda x: x["timestamp"])
            print(f"[INFO] Retrieved {len(historical_data)} data points from Twelve Data")
            return historical_data
            
        except Exception as e:
            print(f"[WARN] Historical data fetch failed for {symbol} from Twelve Data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_market_summary(self, symbol: str) -> Optional[Dict]:
        """Get current market summary. Price from Pyth; volume/cap/change not available."""
        price = self.pyth.get_price(symbol)
        if price is None:
            return None
        return {
            "price": price,
            "volume_24h": None,
            "market_cap": None,
            "percent_change_24h": None,
            "percent_change_7d": None,
        }
    
    def _fetch_candles_from_hub(self, symbol: str, timeframe: str, bar_count: int) -> Optional[List[Candle]]:
        """Fetch candles from hub cache instead of TwelveData directly."""
        try:
            td_symbol = self._symbol_to_twelvedata_symbol(symbol)
            import httpx
            r = httpx.get(
                f"{_hub_url}/api/market/candles",
                params={"symbol": td_symbol, "interval": timeframe},
                timeout=10,
            )
            if r.status_code != 200:
                return None
            raw_candles = r.json().get("candles", [])
            candles = []
            for v in raw_candles:
                try:
                    dt_str = v.get("datetime", "")
                    if not dt_str:
                        continue
                    try:
                        dt = datetime.fromisoformat(dt_str.replace(" ", "T"))
                    except Exception:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    candles.append(Candle(
                        timestamp=dt,
                        open=float(v.get("open", 0)),
                        high=float(v.get("high", 0)),
                        low=float(v.get("low", 0)),
                        close=float(v.get("close", 0)),
                        volume=float(v.get("volume", 0)),
                    ))
                except (ValueError, KeyError):
                    continue
            candles.sort(key=lambda x: x.timestamp)
            result = candles[-bar_count:] if len(candles) > bar_count else candles
            if result:
                print(f"[INFO] Got {len(result)} candles from hub cache")
                return result
        except Exception as e:
            print(f"[WARN] Hub cache fetch failed: {e}")
        return None

    def get_ohlcv_candles(
        self,
        symbol: str,
        timeframe: str,
        bar_count: int
    ) -> Optional[List[Candle]]:
        """
        Fetch OHLCV candles from Twelve Data API

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 15m, 30m, 45m, 1h, 2h, 4h, 8h, 1day, 1week, 1month)
            bar_count: Number of bars to fetch (max 5000)

        Returns:
            List of Candle objects, or None if fetch fails
        """
        # Try hub cache first when HUB_URL is set
        if _hub_url:
            result = self._fetch_candles_from_hub(symbol, timeframe, bar_count)
            if result:
                return result

        try:
            # Convert symbol to Twelve Data format
            td_symbol = self._symbol_to_twelvedata_symbol(symbol)
            
            # Map timeframe to Twelve Data interval format
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "45m": "45min",
                "1h": "1h",
                "2h": "2h",
                "4h": "4h",
                "8h": "8h",
                "1d": "1day",
                "1day": "1day",
                "1w": "1week",
                "1week": "1week",
                "1month": "1month"
            }
            
            interval = interval_map.get(timeframe, "15min")
            
            # Twelve Data time series endpoint for OHLCV
            url = f"{self.TWELVE_DATA_BASE_URL}/time_series"
            params = {
                "symbol": td_symbol,
                "interval": interval,
                "outputsize": min(bar_count, 5000),  # Max 5000 records
                "apikey": self.twelve_data_api_key,
                "format": "JSON"
            }
            
            print(f"[INFO] Fetching {bar_count} {timeframe} candles for {symbol} ({td_symbol}) from Twelve Data...")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for errors
            if "status" in data and data["status"] == "error":
                error_msg = data.get("message", "Unknown error")
                print(f"[ERROR] Twelve Data API error: {error_msg}")
                return None
            
            if "values" not in data:
                print(f"[WARN] No 'values' key in Twelve Data response for {symbol}")
                return None
            
            candles = []
            for value in data["values"]:
                try:
                    # Parse datetime
                    dt_str = value.get("datetime", "")
                    if not dt_str:
                        continue
                    
                    # Handle different datetime formats
                    try:
                        dt = datetime.fromisoformat(dt_str.replace(" ", "T"))
                    except Exception:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    
                    candles.append(Candle(
                        timestamp=dt,
                        open=float(value.get("open", 0)),
                        high=float(value.get("high", 0)),
                        low=float(value.get("low", 0)),
                        close=float(value.get("close", 0)),
                        volume=float(value.get("volume", 0))
                    ))
                except (ValueError, KeyError) as e:
                    print(f"[WARN] Error parsing candle: {e}")
                    continue
            
            # Sort by timestamp (oldest first) and return last N
            candles.sort(key=lambda x: x.timestamp)
            result = candles[-bar_count:] if len(candles) > bar_count else candles
            
            if result:
                print(f"[INFO] Retrieved {len(result)} {timeframe} candles from Twelve Data")
            
            return result if len(result) > 0 else None
        
        except Exception as e:
            print(f"[WARN] OHLCV fetch failed for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch real-time quote for a single symbol from Twelve Data.
        Symbol should be in Twelve Data format (e.g. EUR/USD, BTC/USD).
        """
        try:
            url = f"{self.TWELVE_DATA_BASE_URL}/quote"
            params = {
                "symbol": symbol,
                "apikey": self.twelve_data_api_key,
                "format": "JSON",
                "interval": "1day",
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "error":
                return None
            return data
        except Exception as e:
            print(f"[WARN] Quote fetch failed for {symbol}: {e}")
            return None

    def get_quotes_batch(self, symbols: List[str]) -> List[Dict]:
        """
        Fetch quotes for multiple symbols from Twelve Data (batch).
        Returns list of quote dicts with symbol, name, open, high, low, close, volume, change, percent_change.
        """
        if not symbols:
            return []
        # Twelve Data batch: comma-separated symbols
        symbol_param = ",".join(symbols)
        try:
            url = f"{self.TWELVE_DATA_BASE_URL}/quote"
            params = {
                "symbol": symbol_param,
                "apikey": self.twelve_data_api_key,
                "format": "JSON",
                "interval": "1day",
            }
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            # Batch can return list of objects, or object with "data" array, or keyed by symbol
            out = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("symbol"):
                        out.append(self._normalize_quote(item))
            elif isinstance(data, dict):
                if data.get("status") == "error":
                    return []
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        if isinstance(item, dict) and item.get("symbol"):
                            out.append(self._normalize_quote(item))
                elif "symbol" in data:
                    out.append(self._normalize_quote(data))
                else:
                    for sym, raw in data.items():
                        if isinstance(raw, dict) and raw.get("symbol"):
                            out.append(self._normalize_quote(raw))
            return out
        except Exception as e:
            print(f"[WARN] Batch quote fetch failed: {e}")
            return []

    def _normalize_quote(self, raw: Dict) -> Dict:
        """Normalize Twelve Data quote to common shape."""
        def f(key: str, default=None):
            v = raw.get(key)
            if v is None or v == "":
                return default
            try:
                return float(v)
            except (TypeError, ValueError):
                return default
        return {
            "symbol": raw.get("symbol", ""),
            "name": raw.get("name", raw.get("symbol", "")),
            "open": f("open"),
            "high": f("high"),
            "low": f("low"),
            "close": f("close"),
            "volume": f("volume", 0) or 0,
            "previous_close": f("previous_close"),
            "change": f("change"),
            "percent_change": f("percent_change"),
        }

    def get_funding_data(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """
        Fetch funding rate data (stub - CoinMarketCap doesn't provide this)
        
        In production, fetch from exchange APIs (Binance, etc.)
        
        Args:
            symbol: Trading symbol
            days: Number of days
            
        Returns:
            List of funding rate data points, or None
        """
        # Stub implementation
        # In production, fetch from exchange API
        print(f"[INFO] Funding data not available for {symbol}")
        return None
    
    def get_open_interest_data(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """
        Fetch open interest data (stub - CoinMarketCap doesn't provide this)
        
        In production, fetch from exchange APIs (Binance, etc.)
        
        Args:
            symbol: Trading symbol
            days: Number of days
            
        Returns:
            List of OI data points, or None
        """
        # Stub implementation
        # In production, fetch from exchange API
        print(f"[INFO] Open interest data not available for {symbol}")
        return None
