"""User-server → hub internal callbacks.

Guarded by `X-UserServer-Token` (reuses `INTERNAL_SECRET` at alpha). See
docs/alpha/api-contracts.md §Internal and docs/alpha/plans/connections.md §73-79.

Credits heartbeat / OTel / indexer flush endpoints land on their respective
Phase 4 branches; this router currently exposes only the minimum hub needs
post-wake (credits.py is stubbed, not wired).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..config import settings

router = APIRouter(prefix="/internal/v1", tags=["internal"])


def _auth(request: Request) -> None:
    token = request.headers.get("X-UserServer-Token", "")
    if token != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="invalid user-server token")


@router.post("/credits/heartbeat")
async def credits_heartbeat(request: Request):
    """User-server pings every N seconds with alive-agent count. Phase 4 stub."""
    _auth(request)
    return {"ok": True, "noop": "credits module not yet wired"}


@router.post("/indexer/flush")
async def indexer_flush(request: Request):
    """User-server pushes indexer rows pre-drain. Phase 4 stub."""
    _auth(request)
    return {"ok": True, "noop": "indexer module not yet wired"}


@router.post("/otel/spans")
async def otel_spans(request: Request):
    """User-server pushes OTel spans. Phase 2 stub."""
    _auth(request)
    return {"ok": True, "noop": "otel collector not yet wired"}
