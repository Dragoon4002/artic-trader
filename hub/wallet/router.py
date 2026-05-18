"""Wallet endpoints — per-user 0G wallet for on-chain gas.

GET  /wallet           → address, balance, threshold, runout forecast
POST /wallet/withdraw  → sweep funds back to user-specified address
POST /wallet/preflight → lazy-generate + check gate (called by client before /start)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user
from ..db.base import get_session
from ..db.models.user import User
from . import service

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WalletOut(BaseModel):
    address: str | None
    balance_og: str
    threshold_og: str
    can_start: bool
    burn_rate_og_per_day: str
    runout_at: datetime | None
    cost_per_tx_og: str


@router.get("", response_model=WalletOut)
async def get_wallet(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> WalletOut:
    user = await service.ensure_wallet(db, user)
    balance = service.get_balance_og(user.chain_address or "")
    burn = await service.burn_rate_og_per_day(db, user.id)
    runout = service.forecast_runout(balance, burn)
    return WalletOut(
        address=user.chain_address,
        balance_og=str(balance),
        threshold_og=str(service.MIN_START_OG),
        can_start=service.can_start(balance),
        burn_rate_og_per_day=str(burn),
        runout_at=runout,
        cost_per_tx_og=str(service.cost_per_tx_og()),
    )


class WithdrawRequest(BaseModel):
    to_address: str = Field(min_length=42, max_length=42)
    amount_og: str  # decimal string


class WithdrawResponse(BaseModel):
    tx_hash: str


@router.post("/withdraw", response_model=WithdrawResponse)
async def withdraw(
    body: WithdrawRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> WithdrawResponse:
    user = await service.ensure_wallet(db, user)
    try:
        amount = Decimal(body.amount_og)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid amount_og")
    try:
        tx_hash = await service.withdraw(user, body.to_address, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"withdraw failed: {e}")
    return WithdrawResponse(tx_hash=tx_hash)
