"""Add per-user generated 0G wallet (chain_address, chain_privkey).

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("chain_address", sa.String(), nullable=True))
    op.add_column("users", sa.Column("chain_privkey", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "chain_privkey")
    op.drop_column("users", "chain_address")
