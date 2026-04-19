"""/llm/plan, /llm/supervise, /llm/chat — called by agents via INTERNAL_SECRET."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from ..security import internal_guard
from . import providers, rate_limit

router = APIRouter(prefix="/llm", tags=["llm"], dependencies=[Depends(internal_guard)])


class PlanBody(BaseModel):
    symbol: str
    regime: str | None = None
    candles: list = Field(default_factory=list)
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"


class SuperviseBody(BaseModel):
    position: dict
    context: dict = Field(default_factory=dict)
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"


class ChatBody(BaseModel):
    messages: list[dict]
    provider: str = "openai"
    model: str = "gpt-4o-mini"


def _agent_id(x_agent_id: str | None) -> str | None:
    return x_agent_id


@router.post("/plan")
async def plan(
    body: PlanBody,
    x_agent_id: str | None = Header(default=None, alias="X-Agent-Id"),
) -> dict:
    rate_limit.check_and_count(x_agent_id)
    messages = [
        {"role": "system", "content": "You are a quant strategist. Reply with a strategy name and params."},
        {"role": "user", "content": f"Symbol: {body.symbol}\nRegime: {body.regime or 'unknown'}\nCandles: {body.candles[:10]}"},
    ]
    reply = providers.dispatch(body.provider, messages, body.model)
    return {"reply": reply, "provider": body.provider, "model": body.model}


@router.post("/supervise")
async def supervise(
    body: SuperviseBody,
    x_agent_id: str | None = Header(default=None, alias="X-Agent-Id"),
) -> dict:
    rate_limit.check_and_count(x_agent_id)
    messages = [
        {"role": "system", "content": "You are a risk supervisor. Return KEEP / CLOSE / ADJUST."},
        {"role": "user", "content": f"Position: {body.position}\nContext: {body.context}"},
    ]
    reply = providers.dispatch(body.provider, messages, body.model)
    return {"reply": reply, "provider": body.provider, "model": body.model}


@router.post("/chat")
async def chat(
    body: ChatBody,
    x_agent_id: str | None = Header(default=None, alias="X-Agent-Id"),
) -> dict:
    rate_limit.check_and_count(x_agent_id)
    reply = providers.dispatch(body.provider, body.messages, body.model)
    return {"reply": reply, "provider": body.provider, "model": body.model}
