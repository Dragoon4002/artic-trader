"""Agent ORM — matches docs/alpha/data-model.md user-server.agents."""
from __future__ import annotations

import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime

from ..base import Base

AGENT_STATUSES = ("stopped", "starting", "alive", "stopping", "error")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String, nullable=False)
    llm_model: Mapped[str] = mapped_column(String, nullable=False)
    strategy_pool: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=expression.text("'[]'::jsonb"))
    risk_params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="stopped")
    current_strategy: Mapped[str | None] = mapped_column(String, nullable=True)
    unrealized_pnl_usdt: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
