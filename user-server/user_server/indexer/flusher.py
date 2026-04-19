"""Push batches of indexer_tx rows to hub /internal/v1/indexer/flush.

Called on a 30-min cron (A8 APScheduler) and on-demand during /hub/drain.
Swallows 404 gracefully: hub endpoint doesn't exist yet in alpha — flush
is best-effort until hub zone lands the receiver.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.models import IndexerTx

BATCH_SIZE = 500


def _default_poster() -> Callable[[str, dict], Awaitable[httpx.Response]]:
    async def _post(url: str, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.post(
                url,
                json=payload,
                headers={"X-UserServer-Token": settings.USER_TOKEN, "X-VM-ID": settings.USER_ID},
            )

    return _post


async def flush(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    poster: Callable[[str, dict], Awaitable[httpx.Response]] | None = None,
) -> dict:
    """Push rows newer than `since` to hub. Returns {pushed, skipped, status}."""
    if not settings.HUB_URL:
        return {"pushed": 0, "skipped": 0, "status": "no_hub_url"}

    cutoff = since or (datetime.now(timezone.utc) - timedelta(days=7))
    q = (
        select(IndexerTx)
        .where(IndexerTx.created_at >= cutoff)
        .order_by(IndexerTx.created_at.asc())
        .limit(BATCH_SIZE)
    )
    rows = (await db.execute(q)).scalars().all()
    if not rows:
        return {"pushed": 0, "skipped": 0, "status": "empty"}

    payload = {
        "rows": [
            {
                "tx_hash": r.tx_hash,
                "user_id": str(r.user_id),
                "agent_id": str(r.agent_id),
                "kind": r.kind,
                "amount_usdt": str(r.amount_usdt) if r.amount_usdt is not None else None,
                "block_number": r.block_number,
                "tags": r.tags,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }

    post = poster or _default_poster()
    url = settings.HUB_URL.rstrip("/") + "/internal/v1/indexer/flush"
    try:
        resp = await post(url, payload)
    except httpx.HTTPError as exc:
        return {"pushed": 0, "skipped": len(rows), "status": f"error:{type(exc).__name__}"}

    if resp.status_code == 404:
        return {"pushed": 0, "skipped": len(rows), "status": "hub_endpoint_missing"}
    if resp.status_code >= 400:
        return {"pushed": 0, "skipped": len(rows), "status": f"http_{resp.status_code}"}
    return {"pushed": len(rows), "skipped": 0, "status": "ok"}
