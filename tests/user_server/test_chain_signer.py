"""Chain signer: retry schedule + happy path with a fake JSON-RPC client."""
from __future__ import annotations

import os
import uuid

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@x:5432/x")
os.environ["CHAIN_RPC_URL"] = "http://fake-rpc"
os.environ["CHAIN_ID"] = "31337"
# eth_account requires a valid 32-byte hex key.
os.environ["WALLET_PRIVATE_KEY"] = "0x" + "11" * 32

import pytest  # noqa: E402


class FakeRpc:
    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls: list[dict] = []

    async def post(self, payload: dict) -> dict:
        self.calls.append(payload)
        method = payload["method"]
        for s in self.script:
            if s["method"] == method and not s.get("consumed"):
                s["consumed"] = True
                return s["reply"]
        return {"jsonrpc": "2.0", "id": payload["id"], "result": None}


@pytest.fixture(autouse=True)
def reset_signer():
    from user_server.chain import signer

    signer.set_rpc(None)
    yield
    signer.set_rpc(None)


@pytest.mark.asyncio
async def test_log_decision_success_first_try():
    from user_server.chain import signer

    script = [
        {"method": "eth_getTransactionCount", "reply": {"result": "0x0"}},
        {"method": "eth_gasPrice", "reply": {"result": hex(1_000_000_000)}},
        {"method": "eth_sendRawTransaction", "reply": {"result": "0xabc"}},
        {"method": "eth_getTransactionReceipt", "reply": {"result": {"status": 1}}},
    ]
    rpc = FakeRpc(script)
    signer.set_rpc(rpc)

    outcome = await signer.log_decision(
        session_id=uuid.uuid4(), symbol="BTCUSDT", action=signer.ACTION_TRADE_OPEN
    )
    assert outcome.attempts == 1
    assert outcome.tx_hash == "0xabc"
    assert outcome.receipt["status"] == 1


@pytest.mark.asyncio
async def test_log_decision_retries_on_failure_then_succeeds():
    from user_server.chain import retry, signer

    script = [
        {"method": "eth_getTransactionCount", "reply": {"result": "0x0"}},
        {"method": "eth_gasPrice", "reply": {"result": hex(1_000_000_000)}},
        {"method": "eth_sendRawTransaction", "reply": {"result": "0xfirst"}},
        {"method": "eth_getTransactionReceipt", "reply": {"result": {"status": 0}}},
        {"method": "eth_sendRawTransaction", "reply": {"result": "0xsecond"}},
        {"method": "eth_getTransactionReceipt", "reply": {"result": {"status": 1}}},
    ]
    rpc = FakeRpc(script)
    signer.set_rpc(rpc)

    outcome = await signer.log_decision(
        session_id=uuid.uuid4(), symbol="BTCUSDT", action=signer.ACTION_TRADE_CLOSE
    )
    assert outcome.attempts == 2
    assert outcome.tx_hash == "0xsecond"
    assert outcome.gas_prices[1] > outcome.gas_prices[0]


@pytest.mark.asyncio
async def test_log_decision_exhausts_attempts():
    from user_server.chain import signer

    # 1 nonce + 1 gasPrice, then 3 rounds of (send, receipt-fail)
    script = [
        {"method": "eth_getTransactionCount", "reply": {"result": "0x0"}},
        {"method": "eth_gasPrice", "reply": {"result": hex(1_000_000_000)}},
    ]
    for i in range(3):
        script.append({"method": "eth_sendRawTransaction", "reply": {"result": f"0x{i:064x}"}})
        script.append({"method": "eth_getTransactionReceipt", "reply": {"result": {"status": 0}}})

    rpc = FakeRpc(script)
    signer.set_rpc(rpc)

    outcome = await signer.log_decision(session_id=uuid.uuid4(), symbol="X", action=0)
    assert outcome.attempts == 3
    assert outcome.tx_hash is None
    assert outcome.error is not None
