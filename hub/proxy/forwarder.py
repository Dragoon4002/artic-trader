"""mTLS httpx client — proxies hub requests through to user-server.

Path rewrite: /api/v1/u/<rest> → <vm_endpoint>/<rest>. The hub never forwards raw
client auth headers; it mints an `X-Hub-Secret` header per request.
"""

from __future__ import annotations

import logging
import uuid
from typing import Iterable

import httpx
from fastapi import Request
from fastapi.responses import Response

from ..config import settings

logger = logging.getLogger(__name__)

_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

_STRIPPED_REQUEST = _HOP_BY_HOP | {"authorization", "cookie", "x-api-key"}


class Forwarder:
    """Wrapper around httpx.AsyncClient with timeouts + retry-on-5xx policy."""

    def __init__(self, verify: bool | str = True, cert: tuple[str, str] | None = None):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.PROXY_CONNECT_TIMEOUT_SECONDS,
                read=settings.PROXY_READ_TIMEOUT_SECONDS,
                write=settings.PROXY_READ_TIMEOUT_SECONDS,
                pool=settings.PROXY_CONNECT_TIMEOUT_SECONDS,
            ),
            verify=verify,
            cert=cert,
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def forward(self, request: Request, target_url: str) -> Response:
        """Forward the incoming request to target_url and stream the response back."""
        body = await request.body()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        headers = _filter_headers(request.headers.items(), _STRIPPED_REQUEST)
        headers["X-Hub-Secret"] = settings.INTERNAL_SECRET
        headers["X-Request-ID"] = request_id
        try:
            upstream = await self._client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
                params=dict(request.query_params),
            )
        except httpx.TimeoutException:
            return _error_response(
                504, "UPSTREAM_TIMEOUT", "user-server read timeout", request_id
            )
        except httpx.RequestError as e:
            logger.warning("proxy transport error: %s", e)
            return _error_response(502, "UPSTREAM_UNAVAILABLE", str(e), request_id)

        passthrough_headers = _filter_headers(upstream.headers.items(), _HOP_BY_HOP)
        passthrough_headers["X-Request-ID"] = request_id
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=passthrough_headers,
            media_type=upstream.headers.get("content-type"),
        )


def rewrite_path(incoming_path: str) -> str:
    """`/api/v1/u/agents/xyz` → `/agents/xyz`."""
    prefix = "/api/v1/u"
    if incoming_path.startswith(prefix):
        return incoming_path[len(prefix) :] or "/"
    return incoming_path


def _filter_headers(items: Iterable[tuple[str, str]], drop: set[str]) -> dict[str, str]:
    return {k: v for k, v in items if k.lower() not in drop}


def _error_response(status: int, code: str, message: str, request_id: str) -> Response:
    import json

    body = json.dumps(
        {"error": {"code": code, "message": message, "request_id": request_id}}
    )
    return Response(content=body, status_code=status, media_type="application/json")
