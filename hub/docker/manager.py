"""Docker SDK wrapper for agent containers."""
import docker


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def run(agent_id: str, port: int, env_vars: dict) -> str:
    """Start an agent container. Returns container ID."""
    client = _get_client()
    name = f"artic-agent-{agent_id}"

    # Remove stale container with same name (left over from crash/restart)
    try:
        old = client.containers.get(name)
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    container = client.containers.run(
        "artic-app:latest",
        name=name,
        network="artic-net",
        detach=True,
        environment=env_vars,
        ports={"8000/tcp": port},
        extra_hosts={"host.docker.internal": "host-gateway"},
    )
    return container.id


def stop_and_remove(container_id: str) -> None:
    """Stop and remove a container."""
    client = _get_client()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()
    except docker.errors.NotFound:
        pass


def get_container(container_id: str):
    """Return container object or None."""
    client = _get_client()
    try:
        return client.containers.get(container_id)
    except docker.errors.NotFound:
        return None
