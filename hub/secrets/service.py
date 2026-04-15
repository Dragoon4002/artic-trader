"""Secret management: store, resolve, list."""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models.secret import UserSecret, AgentSecretOverride
from ..db.models.agent import Agent
from ..db.models.user import User
from ..auth.deps import get_current_user

router = APIRouter(prefix="/api/secrets", tags=["secrets"])


class SecretCreate(BaseModel):
    key_name: str
    encrypted_value: str


class AgentSecretCreate(BaseModel):
    key_name: str
    encrypted_value: str


@router.post("")
async def store_secret(
    body: SecretCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Store encrypted key-value in user_secrets."""
    result = await db.execute(
        select(UserSecret).where(
            UserSecret.user_id == user.id, UserSecret.key_name == body.key_name
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.encrypted_value = body.encrypted_value
    else:
        db.add(UserSecret(user_id=user.id, key_name=body.key_name, encrypted_value=body.encrypted_value))
    await db.commit()
    return {"ok": True, "key_name": body.key_name}


@router.get("")
async def list_secrets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List key names only (never return values)."""
    result = await db.execute(
        select(UserSecret.key_name).where(UserSecret.user_id == user.id)
    )
    return {"keys": [row[0] for row in result.all()]}


# Agent-scoped secrets
agent_secrets_router = APIRouter(prefix="/api/agents", tags=["secrets"])


@agent_secrets_router.post("/{agent_id}/secrets")
async def store_agent_secret(
    agent_id: str,
    body: AgentSecretCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    # Verify ownership
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    existing = await db.execute(
        select(AgentSecretOverride).where(
            AgentSecretOverride.agent_id == agent_id,
            AgentSecretOverride.key_name == body.key_name,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.encrypted_value = body.encrypted_value
    else:
        db.add(AgentSecretOverride(agent_id=agent_id, key_name=body.key_name, encrypted_value=body.encrypted_value))
    await db.commit()
    return {"ok": True, "key_name": body.key_name}


_PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


async def store_agent_llm_key(db: AsyncSession, agent_id: str, provider: str | None, api_key: str) -> None:
    """Store LLM API key as agent-level secret override.

    Maps provider name to the correct env var key name.
    If provider is None, stores under a generic key.
    """
    key_name = _PROVIDER_KEY_MAP.get(provider, "LLM_API_KEY") if provider else "LLM_API_KEY"

    existing = await db.execute(
        select(AgentSecretOverride).where(
            AgentSecretOverride.agent_id == agent_id,
            AgentSecretOverride.key_name == key_name,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.encrypted_value = api_key
    else:
        db.add(AgentSecretOverride(agent_id=agent_id, key_name=key_name, encrypted_value=api_key))


async def resolve_secrets(agent_id: str, user_id: str, db: AsyncSession) -> dict:
    """Resolution: agent_secret_overrides -> user_secrets -> env. Returns dict of key_name->value."""
    resolved: dict[str, str] = {}

    # User-level secrets
    result = await db.execute(select(UserSecret).where(UserSecret.user_id == user_id))
    for s in result.scalars().all():
        resolved[s.key_name] = s.encrypted_value

    # Agent overrides (higher priority)
    result = await db.execute(
        select(AgentSecretOverride).where(AgentSecretOverride.agent_id == agent_id)
    )
    for s in result.scalars().all():
        resolved[s.key_name] = s.encrypted_value

    # Env fallback for known keys not in DB
    env_keys = [
        "TWELVE_DATA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "CMC_API_KEY",
        "LLM_PROVIDER", "LLM_MODEL",
    ]
    for key in env_keys:
        if key not in resolved:
            val = os.getenv(key, "")
            if val:
                resolved[key] = val

    return resolved
