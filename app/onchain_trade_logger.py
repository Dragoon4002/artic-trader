"""Log trade executions to 0G Mainnet via TradeLogger contract."""
import os
import json
from typing import Optional
from web3 import Web3

from app.chain_config import get_rpc_url, get_private_key

SIDE_MAP = {"OPEN_LONG": 0, "OPEN_SHORT": 1, "CLOSE_LONG": 2, "CLOSE_SHORT": 3}

PRICE_SCALE = 10**8

ZERO_ADDR = "0x0000000000000000000000000000000000000000"


def _hex_to_bytes(s: str) -> bytes:
    if not s:
        return b""
    s = s.strip()
    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]
    try:
        return bytes.fromhex(s)
    except ValueError:
        return s.encode("utf-8")


class OnchainTradeLogger:
    """Logs trades to 0G TradeLogger contract."""

    def __init__(self):
        rpc = get_rpc_url()
        pk = get_private_key()
        deployed_path = os.path.join(
            os.path.dirname(__file__), "..", "contracts", "trade_logger_deployed.json"
        )

        self._enabled = bool(rpc and pk and os.path.exists(deployed_path))
        if not self._enabled:
            return

        self._w3 = Web3(Web3.HTTPProvider(rpc))
        self._account = self._w3.eth.account.from_key(pk)

        with open(deployed_path) as f:
            deployed = json.load(f)
        self._contract = self._w3.eth.contract(
            address=deployed["address"], abi=deployed["abi"]
        )

    async def log_trade(
        self,
        agent_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        pnl_bps: int,
        detail_json: str,
    ) -> Optional[str]:
        if not self._enabled:
            return None

        import asyncio

        timestamp = int(__import__("time").time())
        session_id = self._w3.keccak(text=f"{agent_id}{symbol}{timestamp}")
        symbol_bytes = self._w3.keccak(text=symbol)[:32]
        side_uint = SIDE_MAP.get(side, 0)
        entry_scaled = int(entry_price * PRICE_SCALE)
        exit_scaled = int(exit_price * PRICE_SCALE)

        og_cid: Optional[str] = None
        try:
            from app.storage import get_client
            payload = json.loads(detail_json) if detail_json else {}
            payload.setdefault("agent_id", agent_id)
            payload.setdefault("symbol", symbol)
            payload.setdefault("side", side)
            cid, _tx = get_client().upload_json(payload)
            og_cid = cid
        except Exception:
            og_cid = None
        detail_hash = self._w3.keccak(text=(f"og:{og_cid}" if og_cid else detail_json))

        try:
            from app.llm.llm_planner import LAST_TEE_SIGNATURE  # type: ignore
        except Exception:
            LAST_TEE_SIGNATURE = ""
        tee_sig_bytes = _hex_to_bytes(LAST_TEE_SIGNATURE)
        tee_provider = os.getenv("ZERO_G_COMPUTE_PROVIDER", "").strip()
        if not (tee_provider and Web3.is_address(tee_provider)):
            tee_provider = ZERO_ADDR
        else:
            tee_provider = Web3.to_checksum_address(tee_provider)

        # Deployed TradeLogger ABI is 7-arg (no TEE fields). Fold TEE into detail_hash
        # by mixing the signature into the keccak input instead of separate args.
        if tee_sig_bytes:
            detail_hash = self._w3.keccak(
                (b"og:" + (og_cid or "").encode() if og_cid else detail_json.encode())
                + b"|tee:" + tee_sig_bytes
            )

        def _send():
            nonce = self._w3.eth.get_transaction_count(self._account.address)
            tx = self._contract.functions.logTrade(
                session_id,
                symbol_bytes,
                side_uint,
                entry_scaled,
                exit_scaled,
                pnl_bps,
                detail_hash,
            ).build_transaction({
                "from": self._account.address,
                "nonce": nonce,
                "gas": 250000,
                "gasPrice": self._w3.eth.gas_price,
            })
            signed = self._account.sign_transaction(tx)
            tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
            return tx_hash.hex()

        return await asyncio.to_thread(_send)
