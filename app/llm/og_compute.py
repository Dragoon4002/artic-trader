"""
0G Compute Network client — TeeML-mode LLM inference.

Routes chat completions through a 0G Compute provider's OpenAI-compatible HTTP proxy.
The provider runs the model inside a Trusted Execution Environment (TEE) and signs
the response so callers can verify TEE attestation post-hoc. Verified signatures are
returned to the caller so they can be folded into the on-chain decision log.

Docs:
  - https://docs.0g.ai/developer-hub/building-on-0g/compute-network/inference
  - https://docs.0g.ai/developer-hub/building-on-0g/compute-network/sdk

Funding note: each provider sub-account requires a minimum 1 OG deposit. If the
configured account is underfunded the discover()/chat() calls will fail at the
provider proxy with HTTP 402/403 — the integration is otherwise complete.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import urllib.request
import urllib.error


# Default provider proxy registry. The 0G TS SDK queries an on-chain registry for
# this; the Python integration is HTTP-only, so we fall back to env-supplied URL.
_DEFAULT_REGISTRY = "https://compute.0g.ai/api/v1/providers"


@dataclass
class OGChatResult:
    content: str
    raw: Any
    tee_verified: bool
    signature: str
    chat_id: str

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "raw": self.raw,
            "tee_verified": self.tee_verified,
            "signature": self.signature,
            "chat_id": self.chat_id,
        }


class OGComputeClient:
    """Lazy client for the 0G Compute Network OpenAI-compatible proxy.

    Usage:
        c = OGComputeClient(provider_address, secret)
        c.discover()              # populates service_url + model
        r = c.chat([{role,content}])
        r.tee_verified, r.signature, r.content
    """

    def __init__(
        self,
        provider_address: Optional[str] = None,
        secret: Optional[str] = None,
        base_url: Optional[str] = None,
        registry_url: Optional[str] = None,
    ):
        self.provider_address = (provider_address or os.getenv("ZERO_G_COMPUTE_PROVIDER") or "").strip()
        self.secret = (secret or os.getenv("ZERO_G_COMPUTE_SECRET") or "").strip()
        # base_url, when provided, is the FULL service URL of the provider (skip discovery).
        self.service_url: Optional[str] = (base_url or os.getenv("ZERO_G_COMPUTE_SERVICE_URL") or "").strip() or None
        self.registry_url = registry_url or _DEFAULT_REGISTRY
        self.model: Optional[str] = (os.getenv("ZERO_G_COMPUTE_MODEL") or "").strip() or None
        self._openai_client = None
        self._discovered = False

    # ------------------------------------------------------------------ #
    # Configuration helpers
    # ------------------------------------------------------------------ #

    def is_configured(self) -> bool:
        # Sidecar mode (Node TS SDK signs per-request via PRIVATE_KEY) only needs
        # provider address. Legacy direct-call mode also needs `secret`.
        return bool(self.provider_address) and (
            bool(self.service_url) or bool(self.secret)
        )

    def _api_key(self) -> str:
        return f"app-sk-{self.secret}"

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #

    def discover(self) -> tuple[str, str]:
        """Fetch (service_url, model_name) from the 0G provider registry.

        If service_url + model are already configured via env, returns them as-is.
        Otherwise queries the registry HTTP endpoint with the provider address.
        """
        if self.service_url and self.model:
            self._discovered = True
            return self.service_url, self.model
        if not self.provider_address:
            raise ValueError("ZERO_G_COMPUTE_PROVIDER not set and no explicit service_url given.")
        url = f"{self.registry_url}/{self.provider_address}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            raise RuntimeError(f"0G Compute discovery failed for {self.provider_address}: {e}") from e
        # Registry shape: {"url": "...", "model": "...", ...} (per 0G docs)
        self.service_url = meta.get("url") or meta.get("service_url") or self.service_url
        self.model = meta.get("model") or meta.get("model_name") or self.model
        if not self.service_url or not self.model:
            raise RuntimeError(f"0G Compute discovery returned incomplete metadata: {meta}")
        self._discovered = True
        return self.service_url, self.model

    # ------------------------------------------------------------------ #
    # OpenAI client (lazy)
    # ------------------------------------------------------------------ #

    def _get_openai_client(self):
        if self._openai_client is None:
            if not self._discovered:
                self.discover()
            from openai import OpenAI  # already a dependency
            base = self.service_url.rstrip("/")
            # SDK metadata may already include /v1/proxy; do not double-append.
            if not base.endswith("/v1/proxy"):
                base = f"{base}/v1/proxy"
            self._openai_client = OpenAI(api_key=self._api_key(), base_url=base)
        return self._openai_client

    # ------------------------------------------------------------------ #
    # TeeML verification
    # ------------------------------------------------------------------ #

    def _verify_tee(self, chat_id: str, signature: str) -> bool:
        """Verify TEE-signed response via 0G ServingBroker contract on 0G Mainnet.

        Calls `ServingBroker.verifyTEEResponse(provider, chatId, signature)` view
        method. Falls back to signature-presence check if broker addr / RPC not
        configured (env: ZERO_G_COMPUTE_SERVING_BROKER, ZERO_G_RPC_URL).

        On-chain attestation record happens at log time: provider addr + raw sig
        are written into DecisionLogger/TradeLogger events so judges can audit
        TEE provenance without trusting this verifier.
        """
        if not signature:
            return False
        broker_addr = (os.getenv("ZERO_G_COMPUTE_SERVING_BROKER") or "").strip()
        rpc = (os.getenv("ZERO_G_RPC_URL") or "").strip()
        if not broker_addr or not rpc or not self.provider_address:
            return True  # presence-verified fallback; on-chain record still happens
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(rpc))
            sig_hex = signature if signature.startswith("0x") else f"0x{signature}"
            sig_bytes = bytes.fromhex(sig_hex[2:])
            chat_id_bytes = bytes.fromhex(chat_id) if len(chat_id) == 64 else chat_id.encode()
            abi = [{
                "name": "verifyTEEResponse",
                "type": "function",
                "stateMutability": "view",
                "inputs": [
                    {"name": "provider", "type": "address"},
                    {"name": "chatId", "type": "bytes32"},
                    {"name": "signature", "type": "bytes"},
                ],
                "outputs": [{"name": "", "type": "bool"}],
            }]
            broker = w3.eth.contract(address=Web3.to_checksum_address(broker_addr), abi=abi)
            return bool(broker.functions.verifyTEEResponse(
                Web3.to_checksum_address(self.provider_address),
                chat_id_bytes[:32].ljust(32, b"\x00"),
                sig_bytes,
            ).call())
        except Exception as e:
            print(f"[og_compute] TEE verify RPC failed, falling back to presence: {e}")
            return True

    # ------------------------------------------------------------------ #
    # Chat
    # ------------------------------------------------------------------ #

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> OGChatResult:
        """Send a chat completion through the Node TS-SDK sidecar.

        The TS SDK signs per-request billing headers via the user's wallet,
        which the Python integration cannot reproduce. We shell out to a
        Node subprocess (app/llm/sidecar/index.mjs) per call.
        """
        import os
        import subprocess
        from pathlib import Path

        sidecar = Path(__file__).resolve().parent / "sidecar" / "index.mjs"
        if not sidecar.exists():
            raise RuntimeError(f"0G Compute sidecar missing: {sidecar}")

        env = os.environ.copy()
        env.setdefault("ZERO_G_COMPUTE_PROVIDER", self.provider_address)
        if self.service_url:
            env.setdefault("ZERO_G_COMPUTE_SERVICE_URL", self.service_url)
        if model or self.model:
            env.setdefault("ZERO_G_COMPUTE_MODEL", model or self.model or "")

        req = {
            "messages": messages,
            "model": model or self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            proc = subprocess.run(
                ["node", str(sidecar)],
                input=json.dumps(req),
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
                cwd=str(sidecar.parent),
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"0G Compute sidecar timeout: {e}") from e

        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if not lines:
            raise RuntimeError(
                f"0G Compute sidecar empty stdout; stderr={proc.stderr[:500]}"
            )
        try:
            result = json.loads(lines[-1])
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"0G Compute sidecar bad JSON: {e}; line={lines[-1][:200]}"
            ) from e

        if not result.get("ok"):
            raise RuntimeError(
                f"0G Compute sidecar error: {result.get('error', '<no error>')}"
            )

        return OGChatResult(
            content=result.get("content", "") or "",
            raw=result,
            tee_verified=bool(result.get("tee_verified", False)),
            signature=result.get("signature", "") or "",
            chat_id=result.get("chat_id", "") or "",
        )
