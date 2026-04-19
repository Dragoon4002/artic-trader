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
    agent_id: str
    level: LogLevel
    message: str
    ts: datetime
    fields: dict = Field(default_factory=dict)
