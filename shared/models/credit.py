from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CreditBalance(BaseModel):
    user_id: str
    balance: Decimal
    updated_at: datetime


class CreditLedgerRow(BaseModel):
    id: str
    user_id: str
    delta: Decimal
    reason: str
    created_at: datetime
