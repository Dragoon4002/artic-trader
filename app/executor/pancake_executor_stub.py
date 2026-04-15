"""
Pancake Perps executor stub for BNB AI Engine.
Live execution on Pancake Perps (BNB Chain) is not yet implemented.
This module provides a stub interface compatible with engine.py when live_mode=True.
"""
from typing import Optional

from ..log_buffer import emit as log_emit


def compute_amount(amount_usdt: float, leverage: int, price: float) -> float:
    """Compute order amount in base asset. notional = amount_usdt * leverage, amount = notional / price"""
    notional = amount_usdt * leverage
    return round(notional / price, 6) if price > 0 else 0


class PancakeExecutorStub:
    """
    Stub client for Pancake Perps execution.
    Logs that live execution is not yet implemented; returns stub responses.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or ""
        log_emit(
            "warn",
            "[BNB AI Engine] Live execution not yet implemented for Pancake Perps. "
            "Paper trading only. Real orders will not be placed.",
        )

    def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        leverage: int,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> dict:
        """
        Stub: Log and return empty success response.
        """
        log_emit(
            "warn",
            f"[STUB] place_order ignored: {side} {amount} {symbol} @ {price} "
            "(Pancake Perps not yet implemented)",
        )
        return {"success": True, "stub": True, "message": "Pancake Perps execution not implemented"}

    def get_positions(self, symbol: Optional[str] = None) -> dict:
        """
        Stub: Return empty positions.
        """
        return {"success": True, "order": None, "positions": []}

    def close_position(self, symbol: str, amount: Optional[float] = None) -> dict:
        """
        Stub: Log and return empty success response.
        """
        log_emit(
            "warn",
            f"[STUB] close_position ignored for {symbol} "
            "(Pancake Perps not yet implemented)",
        )
        return {"success": True, "stub": True}

    def upload_ai_log(
        self,
        order_id: str,
        stage: str,
        model: str,
        input_data: dict,
        output_data: dict,
        explanation: str,
    ) -> dict:
        """
        Stub: Log and return success (no actual upload).
        """
        log_emit("warn", f"[STUB] upload_ai_log ignored for order {order_id}")
        return {"success": True, "stub": True}
