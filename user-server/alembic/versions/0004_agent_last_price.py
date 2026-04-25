"""agents: add last_price for live price display.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-26
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("last_price", sa.Numeric(18, 8), nullable=True))


def downgrade() -> None:
    op.drop_column("agents", "last_price")
