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


def _keccak256(data: bytes) -> bytes:
    """keccak256 (NOT NIST sha3-256) — Ethereum / Initia eth-secp256k1."""
    try:
        from eth_hash.auto import keccak  # ships with web3
        return keccak(data)
    except Exception:
        from Crypto.Hash import keccak as _k  # pycryptodome
        h = _k.new(digest_bits=256)
        h.update(data)
        return h.digest()


def _decompress_pubkey(pub33: bytes) -> bytes:
    """Decompress 33-byte secp256k1 pub → 65-byte uncompressed (0x04 || X || Y)."""
    from ecdsa import SECP256k1, VerifyingKey
    vk = VerifyingKey.from_string(pub33, curve=SECP256k1)
    pt = vk.pubkey.point
    x = pt.x().to_bytes(32, "big")
    y = pt.y().to_bytes(32, "big")
    return b"\x04" + x + y


def _eth_address_bech32(pub33: bytes, hrp: str) -> str:
    """Initia eth-secp256k1: keccak256(uncompressed[1:])[-20:] → bech32(hrp, …)."""
    from bech32 import bech32_encode, convertbits
    uncompressed = _decompress_pubkey(pub33)
    addr20 = _keccak256(uncompressed[1:])[-20:]
    five_bit = convertbits(addr20, 8, 5)
    if five_bit is None:
        raise ValueError("convertbits failed")
    return bech32_encode(hrp, five_bit)


def _eip191_prefix(msg: bytes) -> bytes:
    return b"\x19Ethereum Signed Message:\n" + str(len(msg)).encode() + msg


def _verify_with_digest(pub33: bytes, sig: bytes, digest: bytes) -> bool:
    from ecdsa import BadSignatureError, SECP256k1, VerifyingKey
    from ecdsa.util import sigdecode_string
    try:
        vk = VerifyingKey.from_string(pub33, curve=SECP256k1)
        vk.verify_digest(sig, digest, sigdecode=sigdecode_string)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False


def verify_cosmos_adr36(
    address: str,
    message: str,
    signature_b64: str,
    pubkey_b64: str,
) -> bool:
    """Verify an ADR-36-style signature.

    Tries both wallet families that connect to Initia:

    1. Cosmos vanilla (Keplr/Leap, dev fallback wallets):
       address = bech32(ripemd160(sha256(compressed_pub)))
       digest  = sha256(amino_bytes)
    2. Initia eth-secp256k1 (InterwovenKit / Privy-backed):
       address = bech32(keccak256(uncompressed_pub[1:])[-20:])
       digest  = keccak256(amino_bytes) | keccak256(EIP-191(amino_bytes)) |
                 keccak256(EIP-191(plain_message))
    """
    try:
        pubkey_bytes = base64.b64decode(pubkey_b64)
        if len(pubkey_bytes) != 33:
            logger.debug("adr36 verify: pubkey len=%d, expected 33", len(pubkey_bytes))
            return False

        sig = base64.b64decode(signature_b64)
        if len(sig) not in (64, 65):
            logger.debug("adr36 verify: sig len=%d, expected 64 or 65", len(sig))
            return False
        if len(sig) == 65:
            sig = sig[:64]  # drop trailing v byte; we already know the pubkey

        sign_bytes = _adr36_sign_bytes(address, message)
        hrp = _hrp_of(address)

        # Path 1 — Cosmos ADR-36
        try:
            cosmos_addr = _pubkey_to_bech32(pubkey_bytes, hrp)
        except Exception:
            cosmos_addr = None
        if cosmos_addr == address:
            digest = hashlib.sha256(sign_bytes).digest()
            if _verify_with_digest(pubkey_bytes, sig, digest):
                return True
            logger.warning("adr36: cosmos addr matched but sig invalid")

        # Path 2 — Initia eth-secp256k1
        try:
            eth_addr = _eth_address_bech32(pubkey_bytes, hrp)
        except Exception as exc:
            logger.debug("adr36: eth derive failed: %s", exc)
            eth_addr = None
        if eth_addr == address:
            for label, digest in (
                ("keccak(amino)", _keccak256(sign_bytes)),
                ("keccak(eip191(amino))", _keccak256(_eip191_prefix(sign_bytes))),
                ("keccak(eip191(message))", _keccak256(_eip191_prefix(message.encode("utf-8")))),
            ):
                if _verify_with_digest(pubkey_bytes, sig, digest):
                    logger.info("adr36: eth path verified via %s", label)
                    return True
            logger.warning("adr36: eth addr matched but no hash variant verified")

        logger.warning(
            "adr36: no derivation path matched (cosmos=%s eth=%s expected=%s)",
            cosmos_addr, eth_addr, address,
        )
        return False
    except Exception as exc:
        logger.warning("adr36 verify failed: %s", exc)
        return False
