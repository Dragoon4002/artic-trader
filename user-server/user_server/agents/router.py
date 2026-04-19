"""Hub-facing `/agents/*` endpoints. Guarded by X-Hub-Secret."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Agent
from ..security import hub_guard
from . import service

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(hub_guard)])


class CreateAgentBody(BaseModel):
    name: str
    symbol: str
    llm_provider: str
    llm_model: str
    strategy_pool: list = Field(default_factory=list)
    risk_params: dict = Field(default_factory=dict)


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    symbol: str
    llm_provider: str
    llm_model: str
    strategy_pool: list
    risk_params: dict
    status: str
    container_id: str | None
    port: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, a: Agent) -> "AgentOut":
        return cls(
            id=a.id,
            name=a.name,
            symbol=a.symbol,
            llm_provider=a.llm_provider,
            llm_model=a.llm_model,
            strategy_pool=a.strategy_pool,
            risk_params=a.risk_params,
            status=a.status,
            container_id=a.container_id,
            port=a.port,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )


@router.post("", response_model=AgentOut)
async def create_agent(body: CreateAgentBody, db: AsyncSession = Depends(get_session)) -> AgentOut:
    agent = await service.create(
        db,
        name=body.name,
        symbol=body.symbol,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        strategy_pool=body.strategy_pool,
        risk_params=body.risk_params,
    )
    await db.commit()
    await db.refresh(agent)
    return AgentOut.from_row(agent)


@router.get("", response_model=list[AgentOut])
async def list_agents(db: AsyncSession = Depends(get_session)) -> list[AgentOut]:
    agents = await service.list_all(db)
    return [AgentOut.from_row(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)) -> AgentOut:
    agent = await service.get(db, agent_id)
    return AgentOut.from_row(agent)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)) -> None:
    await service.delete(db, agent_id)
    await db.commit()


@router.post("/{agent_id}/start", response_model=AgentOut)
async def start_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)) -> AgentOut:
    agent = await service.start(db, agent_id)
    await db.commit()
    await db.refresh(agent)
    return AgentOut.from_row(agent)


@router.post("/{agent_id}/stop", response_model=AgentOut)
async def stop_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)) -> AgentOut:
    agent = await service.stop(db, agent_id)
    await db.commit()
    await db.refresh(agent)
    return AgentOut.from_row(agent)


@router.post("/start-all", response_model=list[AgentOut])
async def start_all(db: AsyncSession = Depends(get_session)) -> list[AgentOut]:
    agents = await service.start_all(db)
    await db.commit()
    return [AgentOut.from_row(a) for a in agents]


@router.post("/stop-all", response_model=list[AgentOut])
async def stop_all(db: AsyncSession = Depends(get_session)) -> list[AgentOut]:
    agents = await service.stop_all(db)
    await db.commit()
    return [AgentOut.from_row(a) for a in agents]
