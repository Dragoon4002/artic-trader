"""Morph Cloud VM provider.

Implements the 5 ops in docs/alpha/morph-vm.md §2 using raw REST — the Python SDK is
a thin wrapper over the same endpoints and keeps this module dependency-light.
"""

from __future__ import annotations

import logging
import shlex

import httpx

from ..config import settings
from .provider import VMHandle, VMProviderError

logger = logging.getLogger(__name__)


class MorphProvider:
    """Raw-REST Morph adapter. See morph-vm.md §4."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        image_tag: str | None = None,
        hub_url: str | None = None,
    ):
        self.api_key = api_key or settings.MORPH_API_KEY
        self.base_url = (base_url or settings.MORPH_BASE_URL).rstrip("/")
        self.image_tag = image_tag or settings.VM_IMAGE_TAG
        self.hub_url = hub_url or settings.HUB_PUBLIC_URL

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def start(self, snapshot_id: str) -> VMHandle:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.base_url}/api/instance",
                headers=self._headers(),
                json={"snapshot_id": snapshot_id},
            )
        if r.status_code >= 400:
            raise VMProviderError(f"instance start failed: {r.status_code} {r.text}")
        body = r.json()
        vm_id = body.get("id") or body.get("instance_id")
        endpoint = body.get("endpoint", "")
        return VMHandle(vm_id=vm_id, endpoint=endpoint, snapshot_id=snapshot_id)

    async def configure_wake_on_http(self, vm_id: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{self.base_url}/api/instance/{vm_id}/wake-on",
                headers=self._headers(),
                json={"wake_on_http": True, "wake_on_ssh": False},
            )
        if r.status_code >= 400:
            # Non-fatal per morph-vm.md §5 — log and continue; VM hard-stops on TTL instead.
            logger.warning("wake-on config failed: %s %s", r.status_code, r.text)

    async def launch_user_server(
        self, vm_id: str, user_id: str, user_token: str
    ) -> str:
        """Run the user-server container then expose port 80. See morph-vm.md §4.4.

        Image is loaded into the VM by the golden snapshot build (see
        scripts/build_golden_snapshot.py). Image tag is the local docker tag —
        no external registry. AGENT_IMAGE is passed through so user-server
        spawns agents from the sibling image also baked into the snapshot.
        """
        # Golden snapshot only creates the empty `artic` DB — Alembic runs at
        # wake time so user-server finds its schema on first boot. The baked
        # alembic.ini in the v0 image has host-relative paths, so we bypass
        # the ini entirely and drive alembic programmatically.
        py_migrate = (
            "from alembic.config import Config; from alembic import command; "
            "c=Config(); "
            "c.set_main_option('script_location','/app/alembic'); "
            "c.set_main_option('prepend_sys_path','/app'); "
            "command.upgrade(c,'head')"
        )
        migrate_cmd = (
            "docker run --rm --network host "
            "-e DATABASE_URL=postgresql+asyncpg://artic:artic@localhost:5432/artic "
            f"artic-user-server:{self.image_tag} python -c \"{py_migrate}\""
        )
        await self._exec(vm_id, migrate_cmd, timeout=120.0)
        # Create a dedicated user-defined bridge so (a) docker embedded DNS
        # resolves agent container names and (b) agents don't collide with
        # user-server on host :8000. user-server stays on --network host so
        # Morph's HTTP tunnel can expose it directly.
        await self._exec(
            vm_id,
            "docker network inspect artic-dev >/dev/null 2>&1 || docker network create artic-dev",
            timeout=30.0,
        )
        run_cmd = (
            "docker rm -f user-server 2>/dev/null; "
            "docker run -d --rm --name user-server "
            "-v /var/run/docker.sock:/var/run/docker.sock "
            "--network host "
            "-e DATABASE_URL=postgresql+asyncpg://artic:artic@localhost:5432/artic "
            f"-e HUB_URL={self.hub_url} "
            f"-e USER_ID={user_id} "
            f"-e USER_TOKEN={user_token} "
            f"-e HUB_SECRET={settings.INTERNAL_SECRET} "
            f"-e INTERNAL_SECRET={settings.INTERNAL_SECRET} "
            f"-e AGENT_IMAGE=artic-agent:{self.image_tag} "
            "-e AGENT_NETWORK=artic-dev "
            "-e USER_SERVER_INTERNAL_URL=http://host.docker.internal:8000 "
            f"artic-user-server:{self.image_tag}"
        )
        await self._exec(vm_id, run_cmd, timeout=120.0)
        # Health poll before exposing — fixes the morph-server.md §4 502-race.
        await self._exec(
            vm_id,
            "for i in $(seq 1 30); do curl -fs http://localhost:8000/health && exit 0; sleep 1; done; exit 1",
            timeout=45.0,
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{self.base_url}/api/instance/{vm_id}/http",
                headers=self._headers(),
                json={"name": "user-server", "port": 8000},
            )
        if r.status_code >= 400:
            raise VMProviderError(f"exposeHttpService failed: {r.status_code} {r.text}")
        body = r.json()
        services = body.get("networking", {}).get("http_services", [])
        url = next(
            (s.get("url") for s in services if s.get("name") == "user-server"), ""
        )
        if not url:
            raise VMProviderError(f"exposeHttpService returned no url: {body}")
        return url

    async def snapshot(self, vm_id: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{self.base_url}/api/instance/{vm_id}/snapshot",
                headers=self._headers(),
            )
        if r.status_code >= 400:
            raise VMProviderError(f"snapshot failed: {r.status_code} {r.text}")
        return r.json()["id"]

    async def stop(self, vm_id: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.delete(
                f"{self.base_url}/api/instance/{vm_id}",
                headers=self._headers(),
            )
        if r.status_code >= 400 and r.status_code != 404:
            raise VMProviderError(f"stop failed: {r.status_code} {r.text}")

    async def delete_snapshot(self, snapshot_id: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.delete(
                f"{self.base_url}/api/snapshot/{snapshot_id}",
                headers=self._headers(),
            )
        if r.status_code >= 400 and r.status_code != 404:
            # Per morph-vm.md §5: never block wake on cleanup; log only.
            logger.warning("snapshot delete failed: %s %s", r.status_code, r.text)

    async def health(self, endpoint: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{endpoint.rstrip('/')}/health")
            return r.status_code == 200
        except Exception:
            return False

    async def get_status(self, vm_id: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/api/instance/{vm_id}",
                    headers=self._headers(),
                )
        except Exception as e:
            logger.warning("get_status %s failed: %s", vm_id, e)
            return None
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            logger.warning("get_status %s non-200: %s %s", vm_id, r.status_code, r.text)
            return None
        return r.json().get("status")

    async def _exec(self, vm_id: str, script: str, timeout: float) -> None:
        """Run `script` as a bash login-shell command.

        Morph's /exec endpoint takes `command` as a list but **joins the
        elements with spaces** before passing the result to `bash -c`, so argv
        semantics don't apply. We pre-quote the whole thing with shlex so
        Morph's join doesn't shred our quoting, then wrap in bash -lc to pick
        up the profile PATH inside the VM (docker, psql, etc.).
        """
        wrapped = f"bash -lc {shlex.quote(script)}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self.base_url}/api/instance/{vm_id}/exec",
                headers=self._headers(),
                json={"command": [wrapped]},
            )
        if r.status_code >= 400:
            raise VMProviderError(f"exec failed: {r.status_code} {r.text}")
        body = r.json()
        if body.get("exit_code", 0) != 0:
            raise VMProviderError(f"exec non-zero: {body}")
