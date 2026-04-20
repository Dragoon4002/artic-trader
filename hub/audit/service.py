"""Append-only audit log. Never update or delete rows."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..db import base as db_base
from ..db.models.audit_log import AuditLog


async def record(
    actor: str,
    action: str,
    target: str | None = None,
    detail: dict | None = None,
    *,
    db: AsyncSession | None = None,
) -> None:
    """Append one audit row. Pass `db` to join an existing transaction, else self-manage."""
    row = AuditLog(
        actor=actor,
        action=action,
        target=target,
        detail=detail,
        ts=datetime.now(timezone.utc),
    )
    if db is None:
        async with db_base.async_session() as s:
            s.add(row)
            await s.commit()
    else:
        db.add(row)
