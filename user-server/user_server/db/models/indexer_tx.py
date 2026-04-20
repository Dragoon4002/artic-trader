"""IndexerTx ORM — local mirror of on-chain tx rows; pushed to hub in batches."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from ..base import Base

INDEXER_KINDS = ("trades", "supervise")


class IndexerTx(Base):
    __tablename__ = "indexer_tx"

    tx_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    amount_usdt: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    block_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
