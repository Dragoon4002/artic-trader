from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class StrategySource(StrEnum):
    BUILTIN = "builtin"
    LLM = "llm"
    USER = "user"


class StrategyPlan(BaseModel):
    id: str
    name: str
    source: StrategySource
    params: dict = Field(default_factory=dict)
