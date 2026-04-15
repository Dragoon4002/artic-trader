"""HashKey Global exchange executor."""
import os
import time
import hmac
import hashlib
import httpx
from typing import Optional, Dict, Any
from .base import BaseExecutor
from ..log_buffer import emit as log_emit


class HashKeyExecutor(BaseExecutor):
    """HashKey Global REST API executor.

    Implements BaseExecutor ABC for live trading on HashKey Global exchange.
    Uses HMAC-SHA256 signature authentication.
    """

    def __init__(self):
        self._api_key = os.getenv("HASHKEY_API_KEY", "")
        self._secret = os.getenv("HASHKEY_SECRET", "")
        sandbox = os.getenv("HASHKEY_SANDBOX", "true").lower() == "true"
        self._base_url = (
            "https://api-glb-sandbox.hashkey.com"
            if sandbox else "https://api-pro.hashkey.com"
        )
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self):
        """Ensure httpx client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

    def _sign(self, params: dict) -> dict:
        """Add timestamp + HMAC-SHA256 signature to params.

        HashKey Global signature format:
        - Add timestamp in milliseconds
        - Sort params by key
        - Create query string
        - Sign with HMAC-SHA256
        """
        params["timestamp"] = str(int(time.time() * 1000))
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        sig = hmac.new(
            self._secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = sig
        return params

    def _headers(self) -> dict:
        """Get request headers with API key."""
        return {"X-HK-APIKEY": self._api_key, "Content-Type": "application/json"}

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol from BTC/USD format to BTCUSDT format.

        HashKey Global uses format like BTCUSDT (no separator).
        """
        # Remove common separators
        symbol = symbol.replace("/", "").replace("-", "").replace("_", "")
        # Convert USD to USDT if needed
        if symbol.endswith("USD") and not symbol.endswith("USDT"):
            symbol = symbol[:-3] + "USDT"
        return symbol.upper()

    async def open_long(self, symbol: str, size_usdt: float, leverage: int,
                        tp_price: Optional[float] = None, sl_price: Optional[float] = None):
        """Open a long position.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)
            size_usdt: Position size in USDT
            leverage: Leverage multiplier
            tp_price: Take profit price (optional)
            sl_price: Stop loss price (optional)
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        # Set leverage first
        await self.set_leverage(symbol, leverage)

        # Calculate quantity from size_usdt
        # For futures: quantity = size_usdt / current_price * leverage
        # Simplified: we'll use size_usdt directly as notional value
        params = {
            "symbol": symbol_normalized,
            "side": "BUY",
            "type": "MARKET",
            "quantity": str(size_usdt),  # HashKey API may use different quantity calculation
        }

        # Add TP/SL if provided
        if tp_price is not None:
            params["takeProfit"] = str(tp_price)
        if sl_price is not None:
            params["stopLoss"] = str(sl_price)

        signed_params = self._sign(params)

        try:
            resp = await self._client.post(
                f"{self._base_url}/api/v1/order",
                headers=self._headers(),
                json=signed_params
            )
            resp.raise_for_status()
            result = resp.json()
            log_emit("action", f"[HASHKEY] Long opened: {result}")
            return result
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to open long: {e}")
            raise

    async def open_short(self, symbol: str, size_usdt: float, leverage: int,
                         tp_price: Optional[float] = None, sl_price: Optional[float] = None):
        """Open a short position.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)
            size_usdt: Position size in USDT
            leverage: Leverage multiplier
            tp_price: Take profit price (optional)
            sl_price: Stop loss price (optional)
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        # Set leverage first
        await self.set_leverage(symbol, leverage)

        params = {
            "symbol": symbol_normalized,
            "side": "SELL",
            "type": "MARKET",
            "quantity": str(size_usdt),
        }

        # Add TP/SL if provided
        if tp_price is not None:
            params["takeProfit"] = str(tp_price)
        if sl_price is not None:
            params["stopLoss"] = str(sl_price)

        signed_params = self._sign(params)

        try:
            resp = await self._client.post(
                f"{self._base_url}/api/v1/order",
                headers=self._headers(),
                json=signed_params
            )
            resp.raise_for_status()
            result = resp.json()
            log_emit("action", f"[HASHKEY] Short opened: {result}")
            return result
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to open short: {e}")
            raise

    async def close_position(self, symbol: str):
        """Close current position for symbol.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        # Get current position to determine size and side
        position = await self.get_position(symbol)
        if not position or position.get("positionAmt") == 0:
            log_emit("warn", f"[HASHKEY] No position to close for {symbol_normalized}")
            return

        # Place opposing market order to close
        position_amt = float(position.get("positionAmt", 0))
        side = "SELL" if position_amt > 0 else "BUY"
        quantity = abs(position_amt)

        params = {
            "symbol": symbol_normalized,
            "side": side,
            "type": "MARKET",
            "quantity": str(quantity),
            "reduceOnly": "true",  # Ensure we're only closing, not opening opposite
        }

        signed_params = self._sign(params)

        try:
            resp = await self._client.post(
                f"{self._base_url}/api/v1/order",
                headers=self._headers(),
                json=signed_params
            )
            resp.raise_for_status()
            result = resp.json()
            log_emit("action", f"[HASHKEY] Position closed: {result}")
            return result
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to close position: {e}")
            raise

    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for symbol.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)

        Returns:
            Position data dict or None
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        params = {"symbol": symbol_normalized}
        signed_params = self._sign(params)

        try:
            resp = await self._client.get(
                f"{self._base_url}/api/v1/positions",
                headers=self._headers(),
                params=signed_params
            )
            resp.raise_for_status()
            result = resp.json()

            # Filter for the specific symbol
            if isinstance(result, list):
                for pos in result:
                    if pos.get("symbol") == symbol_normalized:
                        return pos
            elif isinstance(result, dict) and result.get("symbol") == symbol_normalized:
                return result

            return None
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to get position: {e}")
            return None

    async def get_balance(self) -> Optional[Dict[str, Any]]:
        """Get account balance.

        Returns:
            Account balance data dict or None
        """
        await self._ensure_client()

        params = {}
        signed_params = self._sign(params)

        try:
            resp = await self._client.get(
                f"{self._base_url}/api/v1/account",
                headers=self._headers(),
                params=signed_params
            )
            resp.raise_for_status()
            result = resp.json()
            log_emit("tick", f"[HASHKEY] Balance: {result}")
            return result
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to get balance: {e}")
            return None

    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for symbol.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)
            leverage: Leverage multiplier (1-125)
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        params = {
            "symbol": symbol_normalized,
            "leverage": str(leverage),
        }
        signed_params = self._sign(params)

        try:
            resp = await self._client.post(
                f"{self._base_url}/api/v1/leverage",
                headers=self._headers(),
                json=signed_params
            )
            resp.raise_for_status()
            result = resp.json()
            log_emit("init", f"[HASHKEY] Leverage set to {leverage}x: {result}")
            return result
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to set leverage: {e}")
            raise

    async def get_funding_rate(self, symbol: str) -> Optional[float]:
        """Get current funding rate for symbol.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)

        Returns:
            Funding rate as float or None
        """
        await self._ensure_client()
        symbol_normalized = self._normalize_symbol(symbol)

        params = {"symbol": symbol_normalized}
        signed_params = self._sign(params)

        try:
            resp = await self._client.get(
                f"{self._base_url}/api/v1/fundingRate",
                headers=self._headers(),
                params=signed_params
            )
            resp.raise_for_status()
            result = resp.json()

            # Extract funding rate from response
            if isinstance(result, dict):
                rate = result.get("fundingRate") or result.get("lastFundingRate")
                return float(rate) if rate is not None else None
            elif isinstance(result, list) and len(result) > 0:
                rate = result[0].get("fundingRate") or result[0].get("lastFundingRate")
                return float(rate) if rate is not None else None

            return None
        except Exception as e:
            log_emit("error", f"[HASHKEY] Failed to get funding rate: {e}")
            return None
