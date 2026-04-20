"""Trade ORM — matches docs/alpha/data-model.md user-server.trades."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from ..base import Base

TRADE_SIDES = ("long", "short")
CLOSE_REASONS = ("TP", "SL", "SUPERVISOR", "MANUAL")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    size_usdt: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    pnl_usdt: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    strategy: Mapped[str] = mapped_column(String, nullable=False)
    open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
