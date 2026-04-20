"""Cosmos ADR-36 `signArbitrary` verifier for Initia wallets.

ADR-36 wraps an arbitrary message as a zero-fee SignDoc. We verify:
1. pubkey hashes (ripemd160(sha256(pub))) to the same bech32 address
2. signature over sha256(canonical_sign_bytes) is valid for that pubkey

Uses stdlib hashlib + `ecdsa` + `bech32`. If those deps are missing, the
import will fail loudly — requirements.txt must carry them.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def _ripemd160(data: bytes) -> bytes:
    try:
        h = hashlib.new("ripemd160")
    except ValueError as exc:  # some distros disable ripemd160
        raise RuntimeError("ripemd160 unavailable in hashlib; install libssl with legacy") from exc
    h.update(data)
    return h.digest()


def _pubkey_to_bech32(pubkey_bytes: bytes, hrp: str) -> str:
    from bech32 import bech32_encode, convertbits

    sha = hashlib.sha256(pubkey_bytes).digest()
    addr_bytes = _ripemd160(sha)
    five_bit = convertbits(addr_bytes, 8, 5)
    if five_bit is None:
        raise ValueError("convertbits failed")
    return bech32_encode(hrp, five_bit)


def _hrp_of(address: str) -> str:
    if "1" not in address:
        raise ValueError("invalid bech32 address")
    return address.rsplit("1", 1)[0]


def _adr36_sign_bytes(address: str, message: str) -> bytes:
    """Amino JSON sign-doc layout ADR-36 wallets use for signArbitrary.

    Keplr/Leap/Initia wallets all serialize identically here.
    """
    message_b64 = base64.b64encode(message.encode("utf-8")).decode("ascii")
    doc = {
        "chain_id": "",
        "account_number": "0",
        "sequence": "0",
        "fee": {"gas": "0", "amount": []},
        "msgs": [
            {
                "type": "sign/MsgSignData",
                "value": {"signer": address, "data": message_b64},
            }
        ],
        "memo": "",
    }
    # Amino requires sorted keys, no whitespace
    return json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("utf-8")


def verify_cosmos_adr36(
    address: str,
    message: str,
    signature_b64: str,
    pubkey_b64: str,
) -> bool:
    try:
        from ecdsa import BadSignatureError, SECP256k1, VerifyingKey
        from ecdsa.util import sigdecode_string

        pubkey_bytes = base64.b64decode(pubkey_b64)
        # Accept 33-byte compressed secp256k1 pub
        if len(pubkey_bytes) != 33:
            return False
        expected_addr = _pubkey_to_bech32(pubkey_bytes, _hrp_of(address))
        if expected_addr != address:
            return False

        sig = base64.b64decode(signature_b64)
        if len(sig) != 64:  # compact r||s
            return False

        sign_bytes = _adr36_sign_bytes(address, message)
        digest = hashlib.sha256(sign_bytes).digest()

        vk = VerifyingKey.from_string(pubkey_bytes, curve=SECP256k1, hashfunc=hashlib.sha256)
        try:
            vk.verify_digest(sig, digest, sigdecode=sigdecode_string)
            return True
        except BadSignatureError:
            return False
    except Exception as exc:
        logger.warning("adr36 verify failed: %s", exc)
        return False
