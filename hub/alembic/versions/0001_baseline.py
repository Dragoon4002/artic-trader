"""baseline — alpha Phase 1 hub schema.

Tables created (see docs/alpha/data-model.md):
  users, user_secrets, user_vms, market_cache, audit_log, refresh_tokens
Legacy (deprecated/) tables kept for FK integrity, dropped in indexer branch:
  agents, trades, log_entries, agent_secret_overrides, onchain_decisions, onchain_trades

Revision ID: 0001
Revises:
Create Date: 2026-04-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: 0002_wallet_auth is the first real migration.
    # The original baseline created an email/password users table that was
    # superseded before any environment ran it; keeping this empty avoids the
    # DuplicateTable conflict against 0002 on fresh DBs.
    return
    op.create_table(
        "users",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("api_key_hash", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_secrets",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_name", sa.String, nullable=False),
        sa.Column("encrypted_value", sa.Text, nullable=False),
        sa.UniqueConstraint("user_id", "key_name", name="uq_user_secrets_user_key"),
    )

    op.create_table(
        "user_vms",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("provider_vm_id", sa.String, nullable=True),
        sa.Column("endpoint", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="stopped"),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_tag", sa.String, nullable=True),
        sa.Column("wallet_address", sa.String, nullable=True),
        sa.Column("snapshot_id", sa.String, nullable=True),
    )
    op.create_index("ix_user_vms_status", "user_vms", ["status"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("family_id", sa.String, nullable=False),
        sa.Column("token_hash", sa.String, nullable=False, unique=True),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    op.create_table(
        "market_cache",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("timeframe", sa.String, nullable=False),
        sa.Column("candles", sa.JSON, nullable=True),
        sa.Column("last_fetched", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol", "timeframe", name="uq_market_cache_symbol_tf"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("target", sa.String, nullable=True),
        sa.Column("detail", sa.JSON, nullable=True),
    )
    op.create_index("ix_audit_log_ts", "audit_log", ["ts"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])

    # --- legacy tables (to be removed in indexer/user-vm graduation branch) ---
    op.create_table(
        "agents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False, server_default="Unnamed Agent"),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("amount_usdt", sa.Float, nullable=False, server_default="100.0"),
        sa.Column("leverage", sa.Integer, nullable=False, server_default="5"),
        sa.Column("risk_profile", sa.String, nullable=False, server_default="moderate"),
        sa.Column("primary_timeframe", sa.String, nullable=False, server_default="15m"),
        sa.Column("poll_seconds", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("tp_pct", sa.Float, nullable=True),
        sa.Column("sl_pct", sa.Float, nullable=True),
        sa.Column("tp_sl_mode", sa.String, nullable=False, server_default="fixed"),
        sa.Column("supervisor_interval", sa.Float, nullable=False, server_default="60.0"),
        sa.Column("live_mode", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("max_session_loss_pct", sa.Float, nullable=False, server_default="0.10"),
        sa.Column("llm_provider", sa.String, nullable=True),
        sa.Column("llm_model", sa.String, nullable=True),
        sa.Column("leaderboard_opt_in", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("leaderboard_handle", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="stopped"),
        sa.Column("port", sa.Integer, nullable=True),
        sa.Column("container_id", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "agent_secret_overrides",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("key_name", sa.String, nullable=False),
        sa.Column("encrypted_value", sa.Text, nullable=False),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("side", sa.String, nullable=False),
        sa.Column("entry_price", sa.Numeric, nullable=False),
        sa.Column("exit_price", sa.Numeric, nullable=True),
        sa.Column("size_usdt", sa.Float, nullable=True),
        sa.Column("leverage", sa.Integer, nullable=True),
        sa.Column("pnl", sa.Numeric, nullable=True),
        sa.Column("strategy", sa.String, nullable=True),
        sa.Column("close_reason", sa.String, nullable=True),
        sa.Column("tx_hash", sa.String, nullable=True),
        sa.Column("onchain_tx_hash", sa.String, nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "log_entries",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("level", sa.String, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "onchain_decisions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("session_id", sa.LargeBinary, nullable=False),
        sa.Column("tx_hash", sa.String, nullable=False),
        sa.Column("block_number", sa.BigInteger, nullable=False),
        sa.Column("reasoning_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "onchain_trades",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("tx_hash", sa.String, nullable=False),
        sa.Column("side", sa.String, nullable=False),
        sa.Column("entry_price", sa.Numeric, nullable=False),
        sa.Column("exit_price", sa.Numeric, nullable=True),
        sa.Column("pnl_bps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("detail_json", sa.Text, nullable=False),
        sa.Column("block_number", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    return
    op.drop_table("onchain_trades")
    op.drop_table("onchain_decisions")
    op.drop_table("log_entries")
    op.drop_table("trades")
    op.drop_table("agent_secret_overrides")
    op.drop_table("agents")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_ts", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("market_cache")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_user_vms_status", table_name="user_vms")
    op.drop_table("user_vms")
    op.drop_table("user_secrets")
    op.drop_table("users")
