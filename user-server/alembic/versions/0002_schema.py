"""user-server schema: agents, trades, log_entries, strategies, indexer_tx

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-20

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("llm_provider", sa.String(), nullable=False),
        sa.Column("llm_model", sa.String(), nullable=False),
        sa.Column("strategy_pool", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("risk_params", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("container_id", sa.String(), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'stopped'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("entry_price", sa.Numeric(18, 8), nullable=False),
        sa.Column("exit_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("size_usdt", sa.Numeric(18, 8), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("pnl_usdt", sa.Numeric(18, 8), nullable=True),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("open_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("close_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.String(), nullable=True),
        sa.Column("tx_hash", sa.String(), nullable=True),
    )
    op.create_index("ix_trades_agent_id", "trades", ["agent_id"])

    op.create_table(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_log_entries_agent_id", "log_entries", ["agent_id"])
    op.create_index("ix_log_entries_ts", "log_entries", ["ts"])

    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=True),
        sa.Column("code_blob", sa.Text(), nullable=True),
        sa.Column("marketplace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "indexer_tx",
        sa.Column("tx_hash", sa.String(), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("amount_usdt", sa.Numeric(18, 8), nullable=True),
        sa.Column("block_number", sa.BigInteger(), nullable=False),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_indexer_tx_user_created",
        "indexer_tx",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_indexer_tx_kind_amount",
        "indexer_tx",
        ["kind", sa.text("amount_usdt DESC")],
        postgresql_where=sa.text("amount_usdt IS NOT NULL"),
    )
    op.create_index(
        "ix_indexer_tx_tags_gin",
        "indexer_tx",
        ["tags"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_indexer_tx_tags_gin", table_name="indexer_tx")
    op.drop_index("ix_indexer_tx_kind_amount", table_name="indexer_tx")
    op.drop_index("ix_indexer_tx_user_created", table_name="indexer_tx")
    op.drop_table("indexer_tx")
    op.drop_table("strategies")
    op.drop_index("ix_log_entries_ts", table_name="log_entries")
    op.drop_index("ix_log_entries_agent_id", table_name="log_entries")
    op.drop_table("log_entries")
    op.drop_index("ix_trades_agent_id", table_name="trades")
    op.drop_table("trades")
    op.drop_table("agents")
