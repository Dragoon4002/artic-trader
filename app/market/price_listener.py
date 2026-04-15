"""WS listener for hub price feed. Falls back to direct Pyth on disconnect."""
import asyncio
import json
import logging
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PriceListener:
    """Connects to hub's WS /ws/prices, receives price pushes, stores latest per symbol."""

    def __init__(self, hub_url: str, symbol: str, internal_secret: str = ""):
        # http://hub:9000 → ws://hub:9000/ws/prices
        self._ws_url = hub_url.replace("https://", "wss://").replace("http://", "ws://") + "/ws/prices"
        self._symbol = symbol.upper()
        self._secret = internal_secret
        self._running = False
        self._connected = False
        self._latest_price: Optional[float] = None
        self._price_time: float = 0.0
        self._task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_price(self, symbol: str, max_age_seconds: float = 5.0) -> Optional[float]:
        """Return cached WS price if fresh enough."""
        if (
            self._connected
            and self._latest_price is not None
            and symbol.upper() == self._symbol
            and (time.monotonic() - self._price_time) < max_age_seconds
        ):
            return self._latest_price
        return None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"[PriceListener] Started for {self._symbol}")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"[PriceListener] Stopped for {self._symbol}")

    async def _listen_loop(self):
        try:
            import websockets
        except ImportError:
            logger.warning("[PriceListener] websockets not installed, skipping")
            return

        backoff = 1.0
        while self._running:
            try:
                async with websockets.connect(
                    self._ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    self._connected = True
                    backoff = 1.0
                    logger.info("[PriceListener] Connected to hub price feed")

                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw)
                            if msg.get("type") == "prices":
                                data = msg.get("data", {})
                                if self._symbol in data:
                                    self._latest_price = float(data[self._symbol]["price"])
                                    self._price_time = time.monotonic()
                        except (json.JSONDecodeError, KeyError, TypeError):
                            pass

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._connected = False
                if self._running:
                    logger.warning(f"[PriceListener] Disconnected ({e}), retrying in {backoff}s")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)
