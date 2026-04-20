"""Wake-proxy middleware.

Intercepts every request under `/api/v1/u/*`:
  1. Resolve the caller's user_id (JWT or API key).
  2. Look up that user's VM state in the registry.
  3. If stopped: trigger wake. Wake blocks up to VM_WAKE_TIMEOUT_SECONDS.
  4. If the wake still hasn't finished, return 202 {error:{code:VM_WAKING}} +
     Retry-After: 3 per docs/alpha/plans/connections.md §44-48.
  5. Otherwise forward to user-server via Forwarder and touch `last_active_at`.
"""

from __future__ import annotations

import json
import logging

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from ..auth import service as auth_service
from ..db import base as db_base
from ..db.models.user import User
from ..vm import VMService, WakeResult
from .forwarder import Forwarder, rewrite_path

logger = logging.getLogger(__name__)

_PREFIX = "/api/v1/u"


class WakeProxyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, vm_service: VMService, forwarder: Forwarder):
        super().__init__(app)
        self.vm_service = vm_service
        self.forwarder = forwarder

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(_PREFIX):
            return await call_next(request)

        user_id = await _resolve_user_id(request)
        if not user_id:
            return _error(401, "UNAUTHENTICATED", "missing or invalid credentials")

        state = self.vm_service.registry.get(user_id)
        if state is None:
            return _error(404, "VM_NOT_PROVISIONED", "no VM for user")

        if state.status != "running" or not state.endpoint:
            result = await self.vm_service.wake(user_id)
            if result == WakeResult.PENDING:
                return _error(
                    202,
                    "VM_WAKING",
                    "VM is resuming; retry shortly",
                    headers={"Retry-After": "3"},
                )
            if result == WakeResult.FAILED:
                return _error(503, "VM_ERROR", "VM wake failed")
            state = self.vm_service.registry.get(user_id)
            if state is None or not state.endpoint:
                return _error(503, "VM_ERROR", "VM endpoint missing post-wake")

        target = state.endpoint.rstrip("/") + rewrite_path(request.url.path)
        response = await self.forwarder.forward(request, target)
        if 200 <= response.status_code < 400:
            await self.vm_service.touch(user_id)
        return response


async def _resolve_user_id(request: Request) -> str | None:
    # JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            return auth_service.verify_jwt(auth_header[7:])
        except Exception:
            return None
    # API key
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        hashed = auth_service.hash_api_key(api_key)
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(User).where(User.api_key_hash == hashed))
            ).scalar_one_or_none()
            if row:
                return row.id
    return None


def _error(
    status: int, code: str, message: str, headers: dict | None = None
) -> Response:
    body = json.dumps({"error": {"code": code, "message": message}})
    return Response(
        content=body,
        status_code=status,
        media_type="application/json",
        headers=headers or {},
    )
