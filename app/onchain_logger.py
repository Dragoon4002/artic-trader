"""Log supervisor decisions to 0G Mainnet via DecisionLogger contract."""
import os
import json
from typing import Optional
from web3 import Web3

from app.chain_config import get_rpc_url, get_private_key

STRATEGY_INDEX = {
    "simple_momentum": 0, "dual_momentum": 1,
    "z_score": 2, "bollinger_reversion": 3, "rsi_signal": 4, "stochastic_signal": 5,
    "ma_crossover": 6, "ema_crossover": 7, "macd_signal": 8,
    "atr_breakout": 9, "supertrend": 10,
    "breakout": 11, "donchian_channel": 12, "keltner_bollinger": 13,
    "linear_regression_channel": 14, "kalman_fair_value": 15,
    "hurst_mean_reversion": 16, "vwap_reversion": 17, "twap_deviation": 18,
    "half_trend": 19, "chandelier_exit": 20, "parabolic_sar": 21,
    "dpo": 22, "cmo": 23, "trix": 24,
    "williams_r": 25, "cci": 26, "ultimate_oscillator": 27,
    "ichimoku": 28, "renko_trend": 29, "heikin_ashi_trend": 30,
    "demo_mode": 31,
    "llm_auto": 255,
}

ACTION_MAP = {"HOLD": 0, "OPEN_LONG": 1, "OPEN_SHORT": 2, "CLOSE": 3, "ADJUST": 4}

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


class OnchainLogger:
    """Logs trading decisions to 0G DecisionLogger contract."""

    def __init__(self):
        rpc = get_rpc_url()
        pk = get_private_key()
        deployed_path = os.path.join(
            os.path.dirname(__file__), "..", "contracts", "deployed.json"
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

    async def log_decision(
        self,
        agent_id: str,
        symbol: str,
        action: str,
        strategy: str,
        confidence: int,
        pnl_bps: int,
        reasoning: str,
    ) -> Optional[str]:
        if not self._enabled:
            return None

        import asyncio

        timestamp = int(__import__("time").time())
        session_id = self._w3.keccak(text=f"{symbol}{agent_id}{timestamp}")
        symbol_bytes = self._w3.keccak(text=symbol)[:32]
        action_uint = ACTION_MAP.get(action, 0)
        strategy_uint = STRATEGY_INDEX.get(strategy, 255)

        try:
            from app.llm.llm_planner import LAST_TEE_SIGNATURE  # type: ignore
        except Exception:
            LAST_TEE_SIGNATURE = ""
        try:
            from app.llm.llm_planner import LAST_REASONING_CID  # type: ignore
        except Exception:
            LAST_REASONING_CID = None

        reasoning_payload = f"og:{LAST_REASONING_CID}" if LAST_REASONING_CID else reasoning
        tee_sig_bytes = _hex_to_bytes(LAST_TEE_SIGNATURE)
        # Deployed DecisionLogger ABI is 7-arg. Mix TEE signature into the hash
        # so attestation is bound on-chain even without a dedicated field.
        if tee_sig_bytes:
            reasoning_hash = self._w3.keccak(
                reasoning_payload.encode() + b"|tee:" + tee_sig_bytes
            )
        else:
            reasoning_hash = self._w3.keccak(text=reasoning_payload)

        def _send():
            nonce = self._w3.eth.get_transaction_count(self._account.address)
            tx = self._contract.functions.logDecision(
                session_id,
                symbol_bytes,
                action_uint,
                strategy_uint,
                min(confidence, 100),
                pnl_bps,
                reasoning_hash,
            ).build_transaction(
                {
                    "from": self._account.address,
                    "nonce": nonce,
                    "gas": 250000,
                    "gasPrice": self._w3.eth.gas_price,
                }
            )
            signed = self._account.sign_transaction(tx)
            tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
            return tx_hash.hex()

        return await asyncio.to_thread(_send)
