"""Chain-pluggable signature verifiers.

Each entry: chain_id → Callable[[address, message, signature_b64, pubkey_b64], bool].
Raise nothing; return False on any verification failure. Message is the exact
string the client signed (server rebuilds it from the stored nonce).
"""
from __future__ import annotations

from typing import Callable

from .cosmos_adr36 import verify_cosmos_adr36

Verifier = Callable[[str, str, str, str], bool]

VERIFIERS: dict[str, Verifier] = {
    "initia-testnet": verify_cosmos_adr36,
    "initia-mainnet": verify_cosmos_adr36,
}


def get_verifier(chain: str) -> Verifier | None:
    return VERIFIERS.get(chain)
