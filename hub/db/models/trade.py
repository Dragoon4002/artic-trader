"""Trade ORM model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id"), nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    size_usdt: Mapped[float | None] = mapped_column(Float, nullable=True)
    leverage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pnl: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    strategy: Mapped[str | None] = mapped_column(String, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    onchain_tx_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent = relationship("Agent", back_populates="trades")
