from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class TradeSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class CloseReason(StrEnum):
    TP = "take_profit"
    SL = "stop_loss"
    MANUAL = "manual"
    LIQUIDATION = "liquidation"
    EOD = "end_of_day"


class Trade(BaseModel):
    id: str
    agent_id: str
    symbol: str
    side: TradeSide
    entry_price: Decimal
    exit_price: Decimal | None = None
    size: Decimal
    opened_at: datetime
    closed_at: datetime | None = None
    close_reason: CloseReason | None = None
    pnl: Decimal | None = None
