from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class AgentStatus(IntEnum):
    CREATED = 0
    RUNNING = 1
    PAUSED = 2
    STOPPED = 3
    ERROR = 4


class AgentCreate(BaseModel):
    symbol: str
    strategy_id: str | None = None


class AgentInfo(BaseModel):
    id: str
    user_id: str
    symbol: str
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime


class StartRequest(BaseModel):
    agent_id: str
    params: dict = Field(default_factory=dict)


class StatusResponse(BaseModel):
    agent_id: str
    status: AgentStatus
    detail: str | None = None
