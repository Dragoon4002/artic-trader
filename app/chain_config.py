"""Chain config — Initia-first with backward-compat fallbacks.

Resolves RPC URL / private key / chain ID / explorer base from env, preferring
INITIA_* vars (current naming). Falls back to legacy CHAIN_* and HSK_* names.
"""
import os
from typing import Optional


def get_rpc_url() -> Optional[str]:
    return (
        os.getenv("INITIA_RPC_URL")
        or os.getenv("CHAIN_RPC_URL")
        or os.getenv("HSK_RPC_URL")
        or None
    ) or None


def get_private_key() -> Optional[str]:
    return (
        os.getenv("INITIA_PRIVATE_KEY")
        or os.getenv("CHAIN_PRIVATE_KEY")
        or os.getenv("HSK_PRIVATE_KEY")
        or None
    ) or None


def get_chain_id() -> Optional[str]:
    """Rollup chain ID (e.g. 'artic-1'). Not the L1 'initiation-2'."""
    return os.getenv("INITIA_CHAIN_ID") or os.getenv("CHAIN_ID") or None


def get_explorer_base() -> str:
    """Default to Initia testnet scan; override for own rollup if needed."""
    return os.getenv("INITIA_EXPLORER_BASE", "https://scan.testnet.initia.xyz").rstrip("/")


def explorer_tx_url(tx_hash: str) -> str:
    if not tx_hash:
        return ""
    h = tx_hash if tx_hash.startswith("0x") else f"0x{tx_hash}"
    chain = get_chain_id()
    base = get_explorer_base()
    if chain:
        return f"{base}/{chain}/tx/{h}"
    return f"{base}/tx/{h}"
