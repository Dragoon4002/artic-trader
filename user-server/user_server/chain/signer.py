"""Sign + send tx against DecisionLogger. JSON-RPC client is injectable for tests.

Alpha scope (Q3 default): trades and supervisor decisions both ride DecisionLogger
with action codes distinguishing them. A separate TradeLogger contract is
deferred to the contracts zone.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Awaitable, Callable, Protocol

import httpx

from shared.errors import AuthInvalid, Validation

from ..config import settings
from . import retry, wallet

# Action encoding (fits DecisionLogger action uint8):
ACTION_KEEP = 0
ACTION_BUY = 1
ACTION_SELL = 2
ACTION_TRADE_OPEN = 10
ACTION_TRADE_CLOSE = 11
ACTION_SUPERVISE_KEEP = 20
ACTION_SUPERVISE_CLOSE = 21
ACTION_SUPERVISE_ADJUST = 22


class RpcClient(Protocol):
    async def post(self, payload: dict) -> dict: ...


class _HttpxRpc:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client = httpx.AsyncClient(timeout=20.0)

    async def post(self, payload: dict) -> dict:
        r = await self._client.post(self._url, json=payload)
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._client.aclose()


_rpc: RpcClient | None = None


def get_rpc() -> RpcClient:
    global _rpc
    if _rpc is None:
        if not settings.CHAIN_RPC_URL:
            raise Validation("CHAIN_RPC_URL is empty")
        _rpc = _HttpxRpc(settings.CHAIN_RPC_URL)
    return _rpc


def set_rpc(rpc: RpcClient | None) -> None:
    """Test hook."""
    global _rpc
    _rpc = rpc


def _load_contract() -> tuple[str, list]:
    path = Path(settings.CONTRACTS_PATH)
    if not path.exists():
        raise Validation(f"contracts file missing at {path}")
    data = json.loads(path.read_text())
    return data["address"], data["abi"]


async def _get_nonce(rpc: RpcClient, address: str) -> int:
    res = await rpc.post(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionCount", "params": [address, "pending"]}
    )
    return int(res["result"], 16)


async def _get_gas_price(rpc: RpcClient) -> int:
    res = await rpc.post({"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []})
    return int(res["result"], 16)


async def _send_raw(rpc: RpcClient, raw: str) -> str:
    res = await rpc.post(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": [raw]}
    )
    if "error" in res:
        raise RuntimeError(f"rpc error: {res['error']}")
    return res["result"]


async def _get_receipt(rpc: RpcClient, tx_hash: str) -> dict | None:
    res = await rpc.post(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash]}
    )
    return res.get("result")


def _bytes32(s: str) -> bytes:
    b = s.encode("utf-8")[:32]
    return b + b"\x00" * (32 - len(b))


def _encode_log_decision(
    session_id: uuid.UUID,
    symbol: str,
    action: int,
    strategy: int,
    confidence: int,
    pnl_bps: int,
    reasoning_hash: bytes,
) -> bytes:
    from eth_abi import encode  # noqa: PLC0415
    from eth_utils import keccak  # noqa: PLC0415

    selector = keccak(text="logDecision(bytes32,bytes32,uint8,uint8,uint8,int16,bytes32)")[:4]
    args = encode(
        ["bytes32", "bytes32", "uint8", "uint8", "uint8", "int16", "bytes32"],
        [
            session_id.bytes + b"\x00" * 16,
            _bytes32(symbol),
            action,
            strategy,
            confidence,
            pnl_bps,
            reasoning_hash[:32].ljust(32, b"\x00"),
        ],
    )
    return selector + args


async def log_decision(
    *,
    session_id: uuid.UUID,
    symbol: str,
    action: int,
    strategy: int = 0,
    confidence: int = 0,
    pnl_bps: int = 0,
    reasoning_hash: bytes = b"\x00" * 32,
) -> retry.RetryOutcome:
    """Sign + send logDecision tx to the deployed DecisionLogger contract."""
    from eth_account import Account  # noqa: PLC0415

    rpc = get_rpc()
    pk = wallet.load_private_key()
    if not pk:
        raise AuthInvalid("wallet private key unavailable")
    account = Account.from_key(pk)
    address, _abi = _load_contract()
    data = _encode_log_decision(session_id, symbol, action, strategy, confidence, pnl_bps, reasoning_hash)

    nonce = await _get_nonce(rpc, account.address)
    base_gas_price = await _get_gas_price(rpc)

    async def _send(gas_price: int) -> str:
        tx = {
            "to": address,
            "from": account.address,
            "value": 0,
            "gas": 200_000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": settings.CHAIN_ID,
            "data": "0x" + data.hex(),
        }
        signed = account.sign_transaction(tx)
        return await _send_raw(rpc, "0x" + signed.raw_transaction.hex())

    async def _wait(tx_hash: str) -> dict | None:
        return await _get_receipt(rpc, tx_hash)

    return await retry.with_gas_bump(
        _send, _wait, initial_gas_price=base_gas_price, bump_pct=0.20, max_attempts=3
    )
