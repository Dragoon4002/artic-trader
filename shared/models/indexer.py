from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IndexerKind(StrEnum):
    TRADE = "trade"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    SIGNAL = "signal"


class IndexerTags(BaseModel):
    chain: str | None = None
    venue: str | None = None
    extra: dict = Field(default_factory=dict)


class IndexerTxRow(BaseModel):
    id: str
    kind: IndexerKind
    tx_hash: str
    block_number: int
    ts: datetime
    tags: IndexerTags = Field(default_factory=IndexerTags)
