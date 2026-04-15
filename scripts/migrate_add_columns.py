"""Add missing columns to agents and trades tables in Neon PostgreSQL."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

STATEMENTS = [
    # agents table
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS name VARCHAR DEFAULT 'Unnamed Agent'",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS amount_usdt FLOAT DEFAULT 100.0",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS leverage INTEGER DEFAULT 5",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS risk_profile VARCHAR DEFAULT 'moderate'",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS primary_timeframe VARCHAR DEFAULT '15m'",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS poll_seconds FLOAT DEFAULT 1.0",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS tp_pct FLOAT",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS sl_pct FLOAT",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS tp_sl_mode VARCHAR DEFAULT 'fixed'",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS supervisor_interval FLOAT DEFAULT 60.0",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS live_mode BOOLEAN DEFAULT FALSE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS max_session_loss_pct FLOAT DEFAULT 0.10",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS llm_provider VARCHAR",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS llm_model VARCHAR",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'stopped'",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS port INTEGER",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS container_id VARCHAR",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS leaderboard_opt_in BOOLEAN DEFAULT FALSE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS leaderboard_handle VARCHAR",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # trades table
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS size_usdt FLOAT",
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS leverage INTEGER",
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy VARCHAR",
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS close_reason VARCHAR",
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS tx_hash VARCHAR",
]


async def main():
    import asyncpg

    raw_url = os.getenv("DATABASE_URL", "")
    # asyncpg needs postgresql:// not postgresql+asyncpg://
    url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(url)
    print(f"Connected to {url.split('@')[1].split('/')[0]}")

    for stmt in STATEMENTS:
        try:
            await conn.execute(stmt)
            col = stmt.split("IF NOT EXISTS ")[-1].split(" ")[0]
            print(f"  OK: {col}")
        except Exception as e:
            print(f"  SKIP: {stmt[:60]}... ({e})")

    await conn.close()
    print("Migration complete.")


asyncio.run(main())
