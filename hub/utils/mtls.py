"""Hub CA + per-VM cert minting for mTLS between hub and user-server.

Prod: load CA from `HUB_CA_KEY_PATH` / `HUB_CA_CERT_PATH`. Fail fast if missing.
Dev (ENV=dev): generate a transient self-signed CA at process start so the hub boots
without an operator step. Transient = lost on restart (fine for dev).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from ..config import settings


@dataclass
class MintedCert:
    cert_pem: bytes
    key_pem: bytes


class _CAState:
    key: rsa.RSAPrivateKey | None = None
    cert: x509.Certificate | None = None


_ca = _CAState()


def load_ca() -> None:
    """Call once at startup. Loads CA or generates transient one in dev."""
    if settings.HUB_CA_KEY_PATH and settings.HUB_CA_CERT_PATH:
        key_pem = Path(settings.HUB_CA_KEY_PATH).read_bytes()
        cert_pem = Path(settings.HUB_CA_CERT_PATH).read_bytes()
        _ca.key = serialization.load_pem_private_key(key_pem, password=None)
        _ca.cert = x509.load_pem_x509_certificate(cert_pem)
        return
    if settings.ENV != "dev":
        raise RuntimeError(
            "HUB_CA_KEY_PATH + HUB_CA_CERT_PATH required when ENV != dev"
        )
    _ca.key, _ca.cert = _generate_self_signed_ca()


def mint_vm_cert(vm_id: str, validity_days: int = 30) -> MintedCert:
    """Mint a client cert for a user-VM. Returns PEM key + cert."""
    if _ca.key is None or _ca.cert is None:
        raise RuntimeError("CA not loaded; call load_ca() first")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"vm-{vm_id}")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(_ca.cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=1))
        .not_valid_after(now + dt.timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(_ca.key, hashes.SHA256())
    )
    return MintedCert(
        cert_pem=cert.public_bytes(serialization.Encoding.PEM),
        key_pem=key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )


def ca_cert_pem() -> bytes:
    if _ca.cert is None:
        raise RuntimeError("CA not loaded")
    return _ca.cert.public_bytes(serialization.Encoding.PEM)


def _generate_self_signed_ca() -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "artic-hub-ca-dev")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=1))
        .not_valid_after(now + dt.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(key, hashes.SHA256())
    )
    return key, cert
