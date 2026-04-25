"""Demo-mode injector: fakes trades + PnL drift for live agents on the VM.

Runs as a background process on the user-server VM. Every CYCLE_SECONDS:
  - For each agent in 'alive' status:
    * Random PnL drift in [-DRIFT_RANGE, +DRIFT_RANGE] applied to unrealized_pnl_usdt
    * Inserts 0–3 synthetic trades into the trades table with random side / pnl
    * Generates a 32-byte hex tx_hash (NOT on-chain — looks real in the table)
    * Adds matching log entries

Configurable via env. NOT for production. Stop with `pkill -f demo_pnl_injector`.

Usage on the VM:
    pip install psycopg2-binary  # if not already in image
    INJECTOR_DB_URL='postgres://artic:artic@localhost:5432/artic' \\
        python3 demo_pnl_injector.py &

Toggle realistic mode by setting:
    DRIFT_MIN=1000 DRIFT_MAX=10000 CYCLE_SECONDS=300
"""
from __future__ import annotations

import os
import random
import secrets
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: install psycopg2-binary first: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


DB_URL = os.getenv("INJECTOR_DB_URL", "postgresql://artic:artic@localhost:5432/artic")
CYCLE_SECONDS = int(os.getenv("CYCLE_SECONDS", "300"))
DRIFT_MIN = float(os.getenv("DRIFT_MIN", "1000"))
DRIFT_MAX = float(os.getenv("DRIFT_MAX", "10000"))
TRADE_PROB = float(os.getenv("TRADE_PROB", "0.6"))  # chance per agent per cycle
MAX_TRADES_PER_CYCLE = int(os.getenv("MAX_TRADES_PER_CYCLE", "3"))
STRATEGY_NAMES = [
    "momentum", "dual_momentum", "rsi_signal", "macd_signal",
    "bollinger_reversion", "z_score", "supertrend", "atr_breakout",
    "ema_crossover", "vwap_reversion", "ichimoku", "kalman_fair_value",
]


def fake_tx_hash() -> str:
    """32-byte hex with 0x prefix, looks identical to real ones in the UI."""
    return "0x" + secrets.token_hex(32)


def signed_drift() -> float:
    """Random drift biased slightly positive (60% up, 40% down)."""
    magnitude = random.uniform(DRIFT_MIN, DRIFT_MAX)
    return magnitude if random.random() < 0.6 else -magnitude


def maybe_inject_trade(cur, agent_id: str, agent_symbol: str) -> bool:
    """Insert a fake trade for the agent. Returns True if inserted."""
    if random.random() > TRADE_PROB:
        return False

    side = random.choice(["long", "short"])
    entry = round(random.uniform(0.5, 200.0), 4)
    exit_drift_pct = random.uniform(-0.04, 0.06)  # -4% to +6%
    exit_price = round(entry * (1 + exit_drift_pct), 4)
    size_usdt = random.choice([100, 500, 1000, 2500, 5000])
    leverage = random.choice([1, 3, 5, 10])
    pnl = round(size_usdt * leverage * exit_drift_pct * (1 if side == "long" else -1), 2)
    strategy = random.choice(STRATEGY_NAMES)
    close_reason = random.choice(["TP", "SL", "SUPERVISOR", "MANUAL"])
    open_at = datetime.now(timezone.utc) - timedelta(minutes=random.randint(2, 28))
    close_at = datetime.now(timezone.utc)
    tx_hash = fake_tx_hash()
    trade_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO trades (id, agent_id, side, entry_price, exit_price, size_usdt,
                            leverage, pnl_usdt, strategy, open_at, close_at,
                            close_reason, tx_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            trade_id, agent_id, side, entry, exit_price, size_usdt, leverage,
            pnl, strategy, open_at, close_at, close_reason, tx_hash,
        ),
    )

    # Matching log entries — gives the log stream some life
    log_msg = (
        f"[ACTION] {('OPEN_LONG' if side == 'long' else 'OPEN_SHORT')} "
        f"{agent_symbol} @ ${entry:.2f} size=${size_usdt} lev={leverage}x"
    )
    close_msg = (
        f"[ACTION] CLOSE {side.upper()} {agent_symbol} @ ${exit_price:.2f} "
        f"pnl={pnl:+.2f} USDT — {close_reason}"
    )
    onchain_msg = f"[ACTION] [ON-CHAIN] Trade logged: {tx_hash}"
    for ts, msg in [
        (open_at, log_msg),
        (close_at - timedelta(seconds=2), close_msg),
        (close_at, onchain_msg),
    ]:
        cur.execute(
            """
            INSERT INTO log_entries (id, agent_id, level, message, ts)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), agent_id, "action", msg, ts),
        )
    return True


def drift_pnl(cur, agent_id: str, current_pnl: float | None) -> float:
    """Apply random drift to unrealized_pnl_usdt and persist."""
    base = float(current_pnl or 0.0)
    new_pnl = round(base + signed_drift(), 2)
    cur.execute(
        "UPDATE agents SET unrealized_pnl_usdt = %s WHERE id = %s",
        (new_pnl, agent_id),
    )
    return new_pnl


def cycle(conn) -> None:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, name, symbol, unrealized_pnl_usdt FROM agents WHERE status = 'alive'"
    )
    agents = cur.fetchall()
    if not agents:
        print("[injector] no alive agents — skipping cycle", flush=True)
        return

    for a in agents:
        new_pnl = drift_pnl(cur, a["id"], a["unrealized_pnl_usdt"])
        inserted = 0
        for _ in range(random.randint(0, MAX_TRADES_PER_CYCLE)):
            if maybe_inject_trade(cur, a["id"], a["symbol"]):
                inserted += 1
        print(
            f"[injector] {a['name']:<14} ({a['symbol']:<7}) "
            f"uPnL={new_pnl:+10.2f}  +{inserted} fake trade(s)",
            flush=True,
        )
    conn.commit()


def main() -> None:
    print(f"[injector] DB={DB_URL}  cycle={CYCLE_SECONDS}s  "
          f"drift=[{DRIFT_MIN},{DRIFT_MAX}]  trade_prob={TRADE_PROB}",
          flush=True)
    while True:
        try:
            with psycopg2.connect(DB_URL) as conn:
                cycle(conn)
        except Exception as exc:  # noqa: BLE001
            print(f"[injector] cycle error: {exc}", flush=True)
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
