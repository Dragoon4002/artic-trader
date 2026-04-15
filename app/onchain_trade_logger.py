"""Log trade executions to HashKey Chain via TradeLogger contract."""
import os
import json
from typing import Optional
from web3 import Web3

SIDE_MAP = {"OPEN_LONG": 0, "OPEN_SHORT": 1, "CLOSE_LONG": 2, "CLOSE_SHORT": 3}

PRICE_SCALE = 10**8  # on-chain prices scaled by 1e8


class OnchainTradeLogger:
    """Logs trades to HashKey Chain TradeLogger contract."""

    def __init__(self):
        rpc = os.getenv("HSK_RPC_URL")
        pk = os.getenv("HSK_PRIVATE_KEY")
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
        """Log trade on-chain. Returns tx hash or None if disabled.

        Args:
            agent_id: Agent identifier
            symbol: Trading symbol
            side: OPEN_LONG | OPEN_SHORT | CLOSE_LONG | CLOSE_SHORT
            entry_price: Entry price
            exit_price: Exit price (0 for open events)
            pnl_bps: PnL in basis points (0 for open events)
            detail_json: JSON string of full trade detail (hashed on-chain)
        """
        if not self._enabled:
            return None

        import asyncio

        timestamp = int(__import__("time").time())
        session_id = self._w3.keccak(text=f"{agent_id}{symbol}{timestamp}")
        symbol_bytes = self._w3.keccak(text=symbol)[:32]
        side_uint = SIDE_MAP.get(side, 0)
        entry_scaled = int(entry_price * PRICE_SCALE)
        exit_scaled = int(exit_price * PRICE_SCALE)
        detail_hash = self._w3.keccak(text=detail_json)

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
                "gas": 100000,
                "gasPrice": self._w3.eth.gas_price,
            })
            signed = self._account.sign_transaction(tx)
            tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
            return tx_hash.hex()

        return await asyncio.to_thread(_send)
