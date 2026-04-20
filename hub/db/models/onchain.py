"""OnchainDecision + OnchainTrade ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class OnchainDecision(Base):
    __tablename__ = "onchain_decisions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id"), nullable=False
    )
    session_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    tx_hash: Mapped[str] = mapped_column(String, nullable=False)
    block_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reasoning_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agent = relationship("Agent", back_populates="onchain_decisions")


class OnchainTrade(Base):
    __tablename__ = "onchain_trades"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id"), nullable=False
    )
    tx_hash: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    pnl_bps: Mapped[int] = mapped_column(Integer, default=0)
    detail_json: Mapped[str] = mapped_column(Text, nullable=False)
    block_number: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agent = relationship("Agent", back_populates="onchain_trades")
