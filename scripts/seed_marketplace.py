"""Seed hub marketplace_strategies + a system seeder user.

Run from repo root:
    DATABASE_URL=postgresql://artic:artic@localhost:5432/artic \
        python scripts/seed_marketplace.py

Idempotent: re-running upserts by (name) and skips duplicates.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# Allow `python scripts/seed_marketplace.py` from repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from hub.db.base import async_session  # noqa: E402
from hub.db.models.strategy import MarketplaceStrategy  # noqa: E402
from hub.db.models.user import User  # noqa: E402

SEED_USER_ID = "00000000-0000-0000-0000-000000000001"
SEED_WALLET = "0x0000000000000000000000000000000000000001"
SEED_CHAIN = "0g-mainnet"


STRATEGIES: list[dict] = [
    {
        "name": "Simple Momentum",
        "description": "Trend-follow. Long if last N closes net positive, short otherwise. Best on liquid majors during regime persistence.",
        "code_blob": (
            "def signal(candles, lookback=6, threshold=0.0001):\n"
            "    closes = [c['close'] for c in candles[-lookback:]]\n"
            "    ret = (closes[-1] - closes[0]) / closes[0]\n"
            "    if ret > threshold: return 'long'\n"
            "    if ret < -threshold: return 'short'\n"
            "    return 'flat'\n"
        ),
        "params_schema": {"lookback": {"type": "int", "default": 6}, "threshold": {"type": "float", "default": 0.0001}},
        "sharpe_bps": 1450, "max_dd_bps": 820, "total_return_bps": 3120, "win_rate_bps": 5400, "n_trades": 412,
    },
    {
        "name": "RSI Reversal",
        "description": "Mean-reversion on 14-period RSI. Long oversold (<30), short overbought (>70). Best in range-bound markets.",
        "code_blob": (
            "def signal(candles, period=14, low=30, high=70):\n"
            "    # ... RSI calc omitted for preview\n"
            "    rsi = compute_rsi(candles, period)\n"
            "    if rsi < low: return 'long'\n"
            "    if rsi > high: return 'short'\n"
            "    return 'flat'\n"
        ),
        "params_schema": {"period": {"type": "int", "default": 14}, "low": {"type": "int"}, "high": {"type": "int"}},
        "sharpe_bps": 1120, "max_dd_bps": 950, "total_return_bps": 2480, "win_rate_bps": 5800, "n_trades": 587,
    },
    {
        "name": "MACD Crossover",
        "description": "Classic 12/26/9 MACD line vs signal-line cross. Trend confirmation with momentum filter.",
        "code_blob": "def signal(candles): ...  # MACD cross\n",
        "params_schema": {"fast": {"type": "int", "default": 12}, "slow": {"type": "int", "default": 26}, "signal": {"type": "int", "default": 9}},
        "sharpe_bps": 980, "max_dd_bps": 1120, "total_return_bps": 2010, "win_rate_bps": 4900, "n_trades": 318,
    },
    {
        "name": "Bollinger Reversion",
        "description": "Fade 2σ Bollinger touches when ADX < 20. Skips trend regimes to avoid blow-ups.",
        "code_blob": "def signal(candles): ...  # BB + ADX gate\n",
        "params_schema": {"period": {"type": "int", "default": 20}, "stdev": {"type": "float", "default": 2.0}},
        "sharpe_bps": 1310, "max_dd_bps": 740, "total_return_bps": 2850, "win_rate_bps": 6100, "n_trades": 244,
    },
    {
        "name": "ATR Breakout",
        "description": "Donchian-style breakout normalized by ATR. Stops trail at 2*ATR, asymmetric R:R 1:3.",
        "code_blob": "def signal(candles): ...  # ATR breakout\n",
        "params_schema": {"lookback": {"type": "int", "default": 20}, "atr_mult": {"type": "float", "default": 2.0}},
        "sharpe_bps": 1690, "max_dd_bps": 680, "total_return_bps": 4220, "win_rate_bps": 4200, "n_trades": 178,
    },
    {
        "name": "VWAP Reversion",
        "description": "Fade extreme deviations from session VWAP. Best on intraday timeframes with volume profile.",
        "code_blob": "def signal(candles): ...  # VWAP z-score\n",
        "params_schema": {"z_threshold": {"type": "float", "default": 1.8}},
        "sharpe_bps": 870, "max_dd_bps": 1050, "total_return_bps": 1670, "win_rate_bps": 5500, "n_trades": 692,
    },
    {
        "name": "Supertrend",
        "description": "ATR-based trend filter with dynamic stop. Flip on close-side cross.",
        "code_blob": "def signal(candles): ...  # supertrend\n",
        "params_schema": {"atr_period": {"type": "int", "default": 10}, "mult": {"type": "float", "default": 3.0}},
        "sharpe_bps": 1520, "max_dd_bps": 790, "total_return_bps": 3580, "win_rate_bps": 4700, "n_trades": 196,
    },
    {
        "name": "EMA Crossover",
        "description": "9/21 EMA cross with optional 200-EMA regime filter. Long when fast>slow above regime.",
        "code_blob": "def signal(candles): ...  # EMA cross\n",
        "params_schema": {"fast": {"type": "int", "default": 9}, "slow": {"type": "int", "default": 21}},
        "sharpe_bps": 1080, "max_dd_bps": 920, "total_return_bps": 2240, "win_rate_bps": 5100, "n_trades": 354,
    },
    {
        "name": "Kalman Fair Value",
        "description": "Recursive Kalman estimate of fair price; fade deviations beyond filter variance.",
        "code_blob": "def signal(candles): ...  # kalman residual\n",
        "params_schema": {"q": {"type": "float", "default": 0.001}, "r": {"type": "float", "default": 0.01}},
        "sharpe_bps": 1880, "max_dd_bps": 610, "total_return_bps": 4910, "win_rate_bps": 6500, "n_trades": 142,
    },
    {
        "name": "Funding Rate Carry",
        "description": "Short perp when funding > 0.05% per 8h; long when funding < -0.05%. Carry harvest.",
        "code_blob": "def signal(candles, funding): ...  # funding carry\n",
        "params_schema": {"funding_threshold": {"type": "float", "default": 0.0005}},
        "sharpe_bps": 2210, "max_dd_bps": 480, "total_return_bps": 3870, "win_rate_bps": 7200, "n_trades": 89,
    },
]


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


async def ensure_seed_user(db) -> str:
    existing = (
        await db.execute(select(User).where(User.id == SEED_USER_ID))
    ).scalar_one_or_none()
    if existing:
        return existing.id
    user = User(
        id=SEED_USER_ID,
        wallet_address=SEED_WALLET,
        wallet_chain=SEED_CHAIN,
        init_username="artic-seed",
        init_username_resolved_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    print(f"[seed] created seed user {SEED_USER_ID}")
    return user.id


async def upsert_strategies(db, author_id: str) -> tuple[int, int]:
    inserted = skipped = 0
    for s in STRATEGIES:
        existing = (
            await db.execute(
                select(MarketplaceStrategy).where(MarketplaceStrategy.name == s["name"])
            )
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue
        row = MarketplaceStrategy(
            author_user_id=author_id,
            name=s["name"],
            code_hash=_hash(s["code_blob"]),
            code_blob=s["code_blob"],
            params_schema=s.get("params_schema"),
            description=s["description"],
            installs_count=0,
            reports_count=0,
            delisted=False,
            sharpe_bps=s.get("sharpe_bps"),
            max_dd_bps=s.get("max_dd_bps"),
            total_return_bps=s.get("total_return_bps"),
            win_rate_bps=s.get("win_rate_bps"),
            n_trades=s.get("n_trades"),
        )
        db.add(row)
        inserted += 1
    await db.commit()
    return inserted, skipped


async def main() -> None:
    async with async_session() as db:
        author_id = await ensure_seed_user(db)
        ins, skip = await upsert_strategies(db, author_id)
        print(f"[seed] inserted={ins} skipped={skip} (total={len(STRATEGIES)})")


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main())
