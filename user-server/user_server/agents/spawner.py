"""Docker SDK wrapper for spawning `artic-app` agent containers.

The spawner doesn't touch the DB or the registry — callers (service.py) do.
Kept thin so tests can inject a fake docker client via `get_client()`.
"""
from __future__ import annotations

import uuid
from typing import Protocol

from ..config import settings


class DockerContainer(Protocol):  # structural subset of docker.models.containers.Container
    id: str
    name: str

    def stop(self, timeout: int = ...) -> None: ...
    def remove(self, force: bool = ...) -> None: ...


class DockerClient(Protocol):  # structural subset
    containers: object


_client: DockerClient | None = None


def get_client() -> DockerClient:
    """Return a docker SDK client. Override in tests via `set_client`."""
    global _client
    if _client is None:
        import docker

        if settings.DOCKER_HOST:
            _client = docker.DockerClient(base_url=settings.DOCKER_HOST)
        else:
            _client = docker.from_env()
    return _client


def set_client(client: DockerClient | None) -> None:
    """Test hook."""
    global _client
    _client = client


def container_name(agent_id: uuid.UUID) -> str:
    return f"artic-agent-{agent_id}"


def spawn(agent_id: uuid.UUID, env: dict[str, str]) -> DockerContainer:
    """Start a new agent container on the configured network. Returns the container."""
    client = get_client()
    name = container_name(agent_id)
    container = client.containers.run(  # type: ignore[attr-defined]
        image=settings.AGENT_IMAGE,
        name=name,
        environment=env,
        network=settings.AGENT_NETWORK,
        detach=True,
        restart_policy={"Name": "on-failure", "MaximumRetryCount": 3},
        labels={"artic.role": "agent", "artic.agent_id": str(agent_id)},
    )
    return container


def stop(container_id: str, timeout: int = 30) -> None:
    client = get_client()
    try:
        container = client.containers.get(container_id)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 — already gone is fine
        return
    try:
        container.stop(timeout=timeout)
    finally:
        container.remove(force=True)


def build_env(agent: "AgentRow", internal_secret: str, user_server_url: str) -> dict[str, str]:
    """Compose the env dict per docs/alpha/plans/user-vm.md §Agent env."""
    import json

    return {
        "HUB_AGENT_ID": str(agent.id),
        "SYMBOL": agent.symbol,
        "USER_SERVER_URL": user_server_url,
        "INTERNAL_SECRET": internal_secret,
        "STRATEGY_POOL": json.dumps(agent.strategy_pool or []),
        "LLM_PROVIDER": agent.llm_provider,
        "LLM_MODEL": agent.llm_model,
        "RISK_PARAMS": json.dumps(agent.risk_params or {}),
    }


class AgentRow(Protocol):  # only what build_env needs; avoids circular import with db.models
    id: uuid.UUID
    symbol: str
    strategy_pool: list
    llm_provider: str
    llm_model: str
    risk_params: dict
