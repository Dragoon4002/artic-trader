"""Add user_vms, audit_log, refresh_tokens tables

Revision ID: 0003_vm_audit_refresh
Revises: 0002_wallet_auth
Create Date: 2026-04-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_vms",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("provider_vm_id", sa.String(), nullable=True),
        sa.Column("endpoint", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="stopped"),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_tag", sa.String(), nullable=True),
        sa.Column("wallet_address", sa.String(), nullable=True),
        sa.Column("snapshot_id", sa.String(), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False, index=True),
        sa.Column("target", sa.String(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("family_id", sa.String(), nullable=False, index=True),
        sa.Column("token_hash", sa.String(), unique=True, nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("audit_log")
    op.drop_table("user_vms")
