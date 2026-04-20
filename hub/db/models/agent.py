"""Agent ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    # Identity
    name: Mapped[str] = mapped_column(String, default="Unnamed Agent")
    symbol: Mapped[str] = mapped_column(String, nullable=False)

    # Trading config — ALL persisted so restart needs no input
    amount_usdt: Mapped[float] = mapped_column(Float, default=100.0)
    leverage: Mapped[int] = mapped_column(Integer, default=5)
    risk_profile: Mapped[str] = mapped_column(String, default="moderate")
    primary_timeframe: Mapped[str] = mapped_column(String, default="15m")
    poll_seconds: Mapped[float] = mapped_column(Float, default=1.0)
    tp_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp_sl_mode: Mapped[str] = mapped_column(String, default="fixed")
    supervisor_interval: Mapped[float] = mapped_column(Float, default=60.0)
    live_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    max_session_loss_pct: Mapped[float] = mapped_column(Float, default=0.10)

    # LLM config
    llm_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)

    # Leaderboard (display name comes from user.init_username or shortened address)
    leaderboard_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)

    # Runtime state (set by hub, not user)
    status: Mapped[str] = mapped_column(String, default="stopped")
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="agents")
    trades = relationship("Trade", back_populates="agent", cascade="all, delete-orphan")
    log_entries = relationship(
        "LogEntry", back_populates="agent", cascade="all, delete-orphan"
    )
    secret_overrides = relationship(
        "AgentSecretOverride", back_populates="agent", cascade="all, delete-orphan"
    )
    onchain_decisions = relationship(
        "OnchainDecision", back_populates="agent", cascade="all, delete-orphan"
    )
    onchain_trades = relationship(
        "OnchainTrade", back_populates="agent", cascade="all, delete-orphan"
    )
