"""initial schema: wallet-auth users + all current-hub tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-20

0001_baseline was a no-op. This is the first real migration. Schema covers
everything models/__init__.py re-exports so `alembic upgrade head` leaves a
functional DB matching the current code.

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wallet_address", sa.String(), nullable=False),
        sa.Column("wallet_chain", sa.String(), nullable=False),
        sa.Column("init_username", sa.String(), nullable=True),
        sa.Column("init_username_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("api_key_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("wallet_address", "wallet_chain", name="uq_users_wallet"),
    )

    op.create_table(
        "auth_nonce",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("chain", sa.String(), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_auth_nonce_lookup", "auth_nonce", ["address", "chain", "used_at"]
    )

    op.create_table(
        "auth_session_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_pub", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_nonce", sa.BigInteger(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_auth_session_active", "auth_session_keys", ["user_id", "revoked_at"]
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("amount_usdt", sa.Float(), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("risk_profile", sa.String(), nullable=False),
        sa.Column("primary_timeframe", sa.String(), nullable=False),
        sa.Column("poll_seconds", sa.Float(), nullable=False),
        sa.Column("tp_pct", sa.Float(), nullable=True),
        sa.Column("sl_pct", sa.Float(), nullable=True),
        sa.Column("tp_sl_mode", sa.String(), nullable=False),
        sa.Column("supervisor_interval", sa.Float(), nullable=False),
        sa.Column("live_mode", sa.Boolean(), nullable=False),
        sa.Column("max_session_loss_pct", sa.Float(), nullable=False),
        sa.Column("llm_provider", sa.String(), nullable=True),
        sa.Column("llm_model", sa.String(), nullable=True),
        sa.Column("leaderboard_opt_in", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("container_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("entry_price", sa.Numeric(), nullable=False),
        sa.Column("exit_price", sa.Numeric(), nullable=True),
        sa.Column("size_usdt", sa.Float(), nullable=True),
        sa.Column("leverage", sa.Integer(), nullable=True),
        sa.Column("pnl", sa.Numeric(), nullable=True),
        sa.Column("strategy", sa.String(), nullable=True),
        sa.Column("close_reason", sa.String(), nullable=True),
        sa.Column("tx_hash", sa.String(), nullable=True),
        sa.Column("onchain_tx_hash", sa.String(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "log_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "market_cache",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timeframe", sa.String(), nullable=False),
        sa.Column("candles", sa.JSON(), nullable=True),
        sa.Column("last_fetched", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_secrets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_name", sa.String(), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
    )

    op.create_table(
        "agent_secret_overrides",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("key_name", sa.String(), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
    )

    op.create_table(
        "onchain_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("session_id", sa.LargeBinary(), nullable=False),
        sa.Column("tx_hash", sa.String(), nullable=False),
        sa.Column("block_number", sa.BigInteger(), nullable=False),
        sa.Column("reasoning_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "onchain_trades",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("tx_hash", sa.String(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("entry_price", sa.Numeric(), nullable=False),
        sa.Column("exit_price", sa.Numeric(), nullable=True),
        sa.Column("pnl_bps", sa.Integer(), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=False),
        sa.Column("block_number", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("onchain_trades")
    op.drop_table("onchain_decisions")
    op.drop_table("agent_secret_overrides")
    op.drop_table("user_secrets")
    op.drop_table("market_cache")
    op.drop_table("log_entries")
    op.drop_table("trades")
    op.drop_table("agents")
    op.drop_index("ix_auth_session_active", table_name="auth_session_keys")
    op.drop_table("auth_session_keys")
    op.drop_index("ix_auth_nonce_lookup", table_name="auth_nonce")
    op.drop_table("auth_nonce")
    op.drop_table("users")
