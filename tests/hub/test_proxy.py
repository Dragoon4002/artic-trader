"""Wake-proxy middleware behaviour — stopped→202, running→forward."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.responses import Response
from httpx import ASGITransport, AsyncClient

from hub.auth import service as auth_service
from hub.proxy.forwarder import Forwarder
from hub.proxy.middleware import WakeProxyMiddleware
from hub.vm import VMRegistry, VMService, VMState, WakeResult

pytestmark = pytest.mark.asyncio


class _FakeForwarder(Forwarder):
    def __init__(self):
        self.seen: list[tuple[str, str]] = []

    async def forward(self, request, target_url: str) -> Response:
        self.seen.append((request.method, target_url))
        return Response(
            content=b'{"ok":true}', status_code=200, media_type="application/json"
        )

    async def aclose(self) -> None:
        pass


class _StubVM(VMService):
    def __init__(self, registry: VMRegistry, wake_result: WakeResult):
        self.provider = None  # type: ignore[assignment]
        self.registry = registry
        self.secrets_push = None
        self._wake_locks = {}
        self._wake_result = wake_result
        self.touches: list[str] = []

    async def wake(self, user_id: str) -> WakeResult:
        if self._wake_result == WakeResult.RUNNING:
            self.registry.set_status(user_id, "running", endpoint="http://fake-vm")
        return self._wake_result

    async def touch(self, user_id: str) -> None:
        self.touches.append(user_id)


def _build_app(vm_service: VMService, forwarder: _FakeForwarder) -> FastAPI:
    app = FastAPI()
    app.add_middleware(WakeProxyMiddleware, vm_service=vm_service, forwarder=forwarder)
    return app


async def _asgi(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_missing_auth_returns_401():
    registry = VMRegistry()
    stub = _StubVM(registry, WakeResult.RUNNING)
    fwd = _FakeForwarder()
    app = _build_app(stub, fwd)
    async with await _asgi(app) as c:
        r = await c.get("/api/v1/u/agents/foo")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_unprovisioned_user_returns_404():
    registry = VMRegistry()
    stub = _StubVM(registry, WakeResult.RUNNING)
    fwd = _FakeForwarder()
    app = _build_app(stub, fwd)
    token = auth_service.create_jwt("user-x")
    async with await _asgi(app) as c:
        r = await c.get(
            "/api/v1/u/agents/foo", headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "VM_NOT_PROVISIONED"


async def test_stopped_vm_wakes_then_forwards():
    registry = VMRegistry()
    registry.put(
        VMState(
            user_id="u1",
            provider_vm_id=None,
            endpoint=None,
            status="stopped",
            last_active_at=None,
        )
    )
    stub = _StubVM(registry, WakeResult.RUNNING)
    fwd = _FakeForwarder()
    app = _build_app(stub, fwd)
    token = auth_service.create_jwt("u1")
    async with await _asgi(app) as c:
        r = await c.get(
            "/api/v1/u/agents/foo", headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 200
    assert fwd.seen == [("GET", "http://fake-vm/agents/foo")]
    assert stub.touches == ["u1"]


async def test_pending_wake_returns_202_waking():
    registry = VMRegistry()
    registry.put(
        VMState(
            user_id="u2",
            provider_vm_id=None,
            endpoint=None,
            status="stopped",
            last_active_at=None,
        )
    )
    stub = _StubVM(registry, WakeResult.PENDING)
    fwd = _FakeForwarder()
    app = _build_app(stub, fwd)
    token = auth_service.create_jwt("u2")
    async with await _asgi(app) as c:
        r = await c.get(
            "/api/v1/u/agents/foo", headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 202
    assert r.json()["error"]["code"] == "VM_WAKING"
    assert r.headers.get("Retry-After") == "3"
    assert fwd.seen == []
