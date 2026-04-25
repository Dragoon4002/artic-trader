from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogEntry(BaseModel):
    agent_id: str | None = None  # may be injected at push_router level
    level: str  # accepts any level string; DB stores as-is
    message: str
    ts: datetime
    fields: dict = Field(default_factory=dict)
