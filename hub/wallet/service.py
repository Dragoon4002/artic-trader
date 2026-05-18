"""Per-user 0G wallet — generate, balance, forecast burn, withdraw.

Each user gets one generated EOA on 0G Mainnet. Their VM signs every
DecisionLogger / TradeLogger tx with this key. User funds the address from
their connected wallet; hub signs withdrawals back to a user-supplied address.

Storage today: plaintext on `users.chain_privkey`. TODO: KMS/Fernet wrap.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from eth_account import Account
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from ..config import settings
from ..db.models.agent import Agent
from ..db.models.trade import Trade
from ..db.models.user import User

MIN_START_OG = Decimal("0.2")  # gate threshold before agent.start is allowed
GAS_BUDGET_PER_TX = 250_000  # matches onchain_*_logger.py


def _w3() -> Web3:
    return Web3(Web3.HTTPProvider(settings.ZERO_G_RPC_URL))


async def ensure_wallet(db: AsyncSession, user: User) -> User:
    """Generate + persist a wallet on first call. Idempotent."""
    if user.chain_address and user.chain_privkey:
        return user
    acct = Account.create()
    user.chain_address = acct.address
    user.chain_privkey = acct.key.hex()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def get_balance_og(address: str) -> Decimal:
    """Live balance in OG (1e-18 base units)."""
    if not address:
        return Decimal(0)
    try:
        w3 = _w3()
        wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        return Decimal(wei) / Decimal(10**18)
    except Exception:
        return Decimal(0)


def _gas_price_og() -> Decimal:
    try:
        w3 = _w3()
        return Decimal(w3.eth.gas_price) / Decimal(10**18)
    except Exception:
        return Decimal("0.000000001")  # 1 gwei fallback


def cost_per_tx_og() -> Decimal:
    return _gas_price_og() * Decimal(GAS_BUDGET_PER_TX)


async def burn_rate_og_per_day(
    db: AsyncSession, user_id: str, lookback_days: int = 7
) -> Decimal:
    """Avg burn = (recent tx-emitting trades for this user's agents) * gas cost.

    Trades table on the hub mirrors user-server inserts; we count trade closes
    with a tx_hash as a proxy for on-chain logging activity.
    """
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    q = (
        select(Trade)
        .join(Agent, Agent.id == Trade.agent_id)
        .where(
            Agent.user_id == user_id,
            Trade.tx_hash.is_not(None),
            Trade.closed_at >= since,
        )
    )
    try:
        rows = (await db.execute(q)).scalars().all()
    except Exception:
        rows = []
    if not rows:
        return Decimal(0)
    txs_per_day = Decimal(len(rows)) / Decimal(lookback_days)
    # Decisions are roughly proportional; double-count factor 2 for rough trade+decision.
    return txs_per_day * cost_per_tx_og() * Decimal(2)


def forecast_runout(balance_og: Decimal, burn_per_day: Decimal) -> Optional[datetime]:
    if burn_per_day <= 0 or balance_og <= 0:
        return None
    days = balance_og / burn_per_day
    return datetime.now(timezone.utc) + timedelta(days=float(days))


def can_start(balance_og: Decimal) -> bool:
    return balance_og >= MIN_START_OG


async def withdraw(
    user: User, to_address: str, amount_og: Decimal
) -> str:
    """Sign + send transfer of `amount_og` from user's wallet to `to_address`.

    Returns tx hash. Raises on insufficient balance / invalid addr / RPC error.
    """
    if not user.chain_privkey or not user.chain_address:
        raise ValueError("wallet not generated yet")
    if not Web3.is_address(to_address):
        raise ValueError(f"invalid destination address: {to_address}")
    if amount_og <= 0:
        raise ValueError("amount must be > 0")

    w3 = _w3()
    from_addr = Web3.to_checksum_address(user.chain_address)
    to_addr = Web3.to_checksum_address(to_address)

    bal_wei = w3.eth.get_balance(from_addr)
    amount_wei = int(amount_og * Decimal(10**18))
    gas_price = w3.eth.gas_price
    gas_limit = 21_000
    fee_wei = gas_price * gas_limit
    if amount_wei + fee_wei > bal_wei:
        raise ValueError(
            f"insufficient balance: have {bal_wei}, need {amount_wei + fee_wei}"
        )

    nonce = w3.eth.get_transaction_count(from_addr)
    tx = {
        "from": from_addr,
        "to": to_addr,
        "value": amount_wei,
        "nonce": nonce,
        "gas": gas_limit,
        "gasPrice": gas_price,
        "chainId": int(settings.ZERO_G_CHAIN_ID or 16661),
    }
    signed = w3.eth.account.sign_transaction(tx, user.chain_privkey)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()
