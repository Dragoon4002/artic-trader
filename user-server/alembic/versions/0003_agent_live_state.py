"""agents: add current_strategy + unrealized_pnl_usdt

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("current_strategy", sa.String(), nullable=True))
    op.add_column("agents", sa.Column("unrealized_pnl_usdt", sa.Numeric(18, 8), nullable=True))


def downgrade() -> None:
    op.drop_column("agents", "unrealized_pnl_usdt")
    op.drop_column("agents", "current_strategy")
