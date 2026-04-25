/**
 * Hub auth handshake over ADR-36 (Cosmos arbitrary-message signing).
 *
 * Used by both the InterwovenKit connect flow (persistent wallet) and the
 * dev harness at /auth/test/v1 (ephemeral wallet). Helpers here are
 * signer-agnostic — callers supply their own sign function.
 */

import { secp256k1 } from "@noble/curves/secp256k1"
import { sha256 } from "@noble/hashes/sha2"

export interface BuildMessageArgs {
  chain: string
  address: string
  nonce: string
  session_pub: string
  session_scope: string
  issued_at_iso: string
  session_expires_at_iso: string
}

export function buildSigninMessage(args: BuildMessageArgs): string {
  return (
    `artic.trade wants you to sign in with your ${args.chain} account:\n` +
    `${args.address}\n` +
    `\n` +
    `Session public key: ${args.session_pub}\n` +
    `Scope: ${args.session_scope}\n` +
    `Nonce: ${args.nonce}\n` +
    `Issued At: ${args.issued_at_iso}\n` +
    `Expires At: ${args.session_expires_at_iso}`
  )
}

/** ADR-36 amino SignDoc (keys sorted alphabetically — must match hub rebuild). */
export function buildAdr36SignDoc(address: string, message: string) {
  const msgB64 = b64encode(new TextEncoder().encode(message))
  return {
    account_number: "0",
    chain_id: "",
    fee: { amount: [], gas: "0" },
    memo: "",
    msgs: [
      {
        type: "sign/MsgSignData",
        value: { data: msgB64, signer: address },
      },
    ],
    sequence: "0",
  }
}

export function newSessionKeypair() {
  const priv = secp256k1.utils.randomSecretKey()
  const pub = secp256k1.getPublicKey(priv, true)
  return { priv, pub, pub_b64: b64encode(pub) }
}

export function b64encode(bytes: Uint8Array): string {
  let s = ""
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s)
}

export function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

export function sha256Hex(bytes: Uint8Array): string {
  return hex(sha256(bytes))
}

export interface NonceResponse {
  nonce: string
  issued_at: string
}

export interface VerifyResponse {
  access_token: string
  session_id: string
  init_username: string | null
}

export async function fetchNonce(
  hubUrl: string,
  address: string,
  chain: string,
): Promise<NonceResponse> {
  const r = await fetch(`${hubUrl.replace(/\/+$/, "")}/auth/nonce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ address, chain }),
  })
  const body = await r.json()
  if (!r.ok) throw new Error(`nonce: ${r.status} ${JSON.stringify(body)}`)
  if (!body.issued_at) {
    throw new Error("nonce response missing issued_at — hub patch not deployed")
  }
  return body as NonceResponse
}

export interface VerifyArgs {
  hubUrl: string
  address: string
  chain: string
  nonce: string
  pubkey_b64: string
  signature_b64: string
  session_pub_b64: string
  session_scope: string
  session_expires_at_iso: string
}

export async function verifySignature(a: VerifyArgs): Promise<VerifyResponse> {
  const r = await fetch(`${a.hubUrl.replace(/\/+$/, "")}/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      address: a.address,
      chain: a.chain,
      nonce: a.nonce,
      signature: a.signature_b64,
      pubkey: a.pubkey_b64,
      session_pub: a.session_pub_b64,
      session_scope: a.session_scope,
      session_expires_at: a.session_expires_at_iso,
    }),
  })
  const body = await r.json()
  if (!r.ok) throw new Error(`verify: ${r.status} ${JSON.stringify(body)}`)
  return body as VerifyResponse
}

// ── JWT persistence ─────────────────────────────────────────────────────────

const LS_KEY = "artic_hub_jwt"

export interface StoredJwt {
  access_token: string
  session_id: string
  session_priv_hex: string
  address: string
  init_username: string | null
  exp: number // unix ms
}

export function saveJwt(j: StoredJwt) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(j))
  } catch {
    /* quota / private mode — ignore */
  }
}

export function loadJwt(): StoredJwt | null {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    const j = JSON.parse(raw) as StoredJwt
    if (!j.exp || j.exp < Date.now()) return null
    return j
  } catch {
    return null
  }
}

export function clearJwt() {
  try {
    localStorage.removeItem(LS_KEY)
  } catch {
    /* ignore */
  }
}

/** Decode JWT exp claim to unix-ms (best-effort; returns 0 on failure). */
export function jwtExpMs(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.exp ? payload.exp * 1000 : 0
  } catch {
    return 0
  }
}
