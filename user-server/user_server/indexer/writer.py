"""Write indexer_tx rows after a successful chain tx.

Called by chain.signer on each confirmed receipt. Idempotent by tx_hash PK.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import IndexerTx


async def write(
    db: AsyncSession,
    *,
    tx_hash: str,
    user_id: uuid.UUID,
    agent_id: uuid.UUID,
    kind: str,
    block_number: int,
    tags: dict,
    amount_usdt: Decimal | None = None,
) -> None:
    stmt = pg_insert(IndexerTx).values(
        tx_hash=tx_hash,
        user_id=user_id,
        agent_id=agent_id,
        kind=kind,
        amount_usdt=amount_usdt,
        block_number=block_number,
        tags=tags,
    ).on_conflict_do_nothing(index_elements=["tx_hash"])
    await db.execute(stmt)
    await db.flush()
