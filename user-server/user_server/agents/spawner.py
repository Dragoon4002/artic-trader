"""Docker SDK wrapper for spawning `artic-app` agent containers.

The spawner doesn't touch the DB or the registry — callers (service.py) do.
Kept thin so tests can inject a fake docker client via `get_client()`.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Protocol

from ..config import settings


def _load_env_into_os() -> None:
    """Populate os.environ from project .env files so build_env() sees ZERO_G_*
    and LLM_PROVIDER. Pydantic-Settings loads .env into the Settings model but
    not into os.environ, which build_env relies on for chain/compute config."""
    here = Path(__file__).resolve()
    candidates = []
    # .env.local takes precedence over .env (Next.js convention). Earlier files
    # in this list win because the loader skips keys already set.
    for base in (here.parents[2], here.parents[3], Path.cwd()):
        candidates.append(base / ".env.local")
        candidates.append(base / ".env")
    seen: set[str] = set()
    for env_file in candidates:
        key = str(env_file)
        if key in seen or not env_file.is_file():
            continue
        seen.add(key)
        try:
            for raw in env_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # Skip placeholder values like "<provider_addr>" — they're sentinels, not config.
                if not k or k in os.environ or not v or (v.startswith("<") and v.endswith(">")):
                    continue
                os.environ[k] = v
        except Exception:
            continue


_load_env_into_os()


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
        extra_hosts={"host.docker.internal": "host-gateway"},
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


def build_env(
    agent: "AgentRow",
    internal_secret: str,
    user_server_url: str,
    llm_api_key: str | None = None,
    twelve_data_api_key: str | None = None,
    owner_init_name: str | None = None,
) -> dict[str, str]:
    """Compose the env dict per docs/alpha/plans/user-vm.md §Agent env.

    Forwards 0G mainnet chain + Compute config from user-server env so the
    agent container can sign DecisionLogger / TradeLogger txs and call the
    0G Compute TeeML proxy.
    """
    import json

    chain_env: dict[str, str] = {}
    for key in (
        "ZERO_G_RPC_URL",
        "ZERO_G_PRIVATE_KEY",
        "ZERO_G_CHAIN_ID",
        "ZERO_G_EXPLORER_BASE",
        "ZERO_G_COMPUTE_SECRET",
        "ZERO_G_COMPUTE_PROVIDER",
        "ZERO_G_COMPUTE_SERVING_BROKER",
        "ZERO_G_STORAGE_INDEXER_URL",
    ):
        v = os.getenv(key)
        if v:
            chain_env[key] = v

    return {
        "HUB_AGENT_ID": str(agent.id),
        "SYMBOL": agent.symbol,
        "USER_SERVER_URL": user_server_url,
        "HUB_URL": user_server_url,  # hub_callback reads HUB_URL for push endpoints
        "INTERNAL_SECRET": internal_secret,
        "STRATEGY_POOL": json.dumps(agent.strategy_pool or []),
        # Env LLM_PROVIDER on user-server overrides per-agent stored value —
        # lets a single deployment flip the whole fleet to 0g_compute without
        # touching agent rows. Falls back to agent's stored choice otherwise.
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER") or agent.llm_provider,
        "LLM_MODEL": os.getenv("LLM_MODEL") or agent.llm_model,
        "RISK_PARAMS": json.dumps(agent.risk_params or {}),
        **({"GEMINI_API_KEY": llm_api_key} if llm_api_key else {}),
        **({"TWELVE_DATA_API_KEY": twelve_data_api_key} if twelve_data_api_key else {}),
        **({"OWNER_INIT_NAME": owner_init_name} if owner_init_name else {}),
        **chain_env,
    }


class AgentRow(Protocol):  # only what build_env needs; avoids circular import with db.models
    id: uuid.UUID
    symbol: str
    strategy_pool: list
    llm_provider: str
    llm_model: str
    risk_params: dict
