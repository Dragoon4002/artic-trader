"use client"

/**
 * Hub auth handshake using InterwovenKit as the canonical signer.
 *
 * Flow:
 *   1. user connects via InterwovenKit (kit.openConnect)
 *   2. we fetch a nonce from hub keyed on kit.address
 *   3. we ask kit.offlineSigner.signAmino(address, adr36SignDoc) to sign the
 *      ADR-36 doc — produces a Cosmos-compatible signature + pubkey
 *   4. we POST {pubkey, signature, ...} to /auth/verify
 *
 * Legacy localStorage secp256k1 path is preserved as a dev fallback so the
 * /auth/test/v1 harness keeps working when InterwovenKit isn't mounted.
 */

import { useCallback, useEffect, useRef, useState } from "react"
import { secp256k1 } from "@noble/curves/secp256k1"
import { sha256 } from "@noble/hashes/sha2"
import { ripemd160 } from "@noble/hashes/legacy"
import { bech32 } from "bech32"
import { useInterwovenKit } from "@initia/interwovenkit-react"
import {
  b64encode,
  buildAdr36SignDoc,
  buildSigninMessage,
  clearJwt,
  fetchNonce,
  hex,
  jwtExpMs,
  loadJwt,
  newSessionKeypair,
  saveJwt,
  verifySignature,
  type StoredJwt,
} from "@/lib/hub-auth"

const HUB_URL =
  (process.env.NEXT_PUBLIC_HUB_URL as string | undefined) || "http://localhost:9000"
const CHAIN =
  (process.env.NEXT_PUBLIC_HUB_AUTH_CHAIN as string | undefined) || "initia-testnet"
const HRP = (process.env.NEXT_PUBLIC_HUB_AUTH_HRP as string | undefined) || "init"
const SESSION_SCOPE = "authenticated-actions"
const SESSION_TTL_SECONDS = 8 * 60 * 60

const WALLET_KEY = "artic_hub_wallet_priv_hex"

type Status = "idle" | "running" | "ok" | "error"

type FallbackWallet = { priv: Uint8Array; pub: Uint8Array; address: string }

function loadOrCreateFallbackWallet(): FallbackWallet {
  let privHex: string | null = null
  try {
    privHex = localStorage.getItem(WALLET_KEY)
  } catch {
    /* private mode / disabled */
  }
  let priv: Uint8Array
  if (privHex && /^[0-9a-f]{64}$/i.test(privHex)) {
    priv = new Uint8Array(privHex.match(/.{2}/g)!.map((b) => parseInt(b, 16)))
  } else {
    priv = secp256k1.utils.randomSecretKey()
    try {
      localStorage.setItem(WALLET_KEY, hex(priv))
    } catch {
      /* ignore */
    }
  }
  const pub = secp256k1.getPublicKey(priv, true)
  const sha = sha256(pub)
  const rip = ripemd160(sha)
  const address = bech32.encode(HRP, bech32.toWords(rip))
  return { priv, pub, address }
}

export function useHubAuth() {
  const kit = useInterwovenKit()
  const [fallback, setFallback] = useState<FallbackWallet | null>(null)
  const [token, setToken] = useState<StoredJwt | null>(null)
  const [status, setStatus] = useState<Status>("idle")
  const [error, setError] = useState<string | null>(null)
  const [hydrated, setHydrated] = useState(false)
  const inFlight = useRef(false)

  const activeAddress = kit.isConnected ? kit.address ?? null : fallback?.address ?? null

  // Hydrate fallback wallet + cached JWT on first client render.
  useEffect(() => {
    const w = loadOrCreateFallbackWallet()
    setFallback(w)
    const cached = loadJwt()
    if (cached && cached.exp > Date.now()) {
      setToken(cached)
      setStatus("ok")
    }
    setHydrated(true)
  }, [])

  const run = useCallback(async () => {
    if (inFlight.current) return
    if (!activeAddress) {
      setError("no wallet connected")
      setStatus("error")
      return
    }
    inFlight.current = true
    setStatus("running")
    setError(null)

    try {
      const address = activeAddress
      const nonce = await fetchNonce(HUB_URL, address, CHAIN)

      const session = newSessionKeypair()
      const session_expires_at_iso = new Date(
        Date.now() + SESSION_TTL_SECONDS * 1000,
      ).toISOString()

      const message = buildSigninMessage({
        chain: CHAIN,
        address,
        nonce: nonce.nonce,
        session_pub: session.pub_b64,
        session_scope: SESSION_SCOPE,
        issued_at_iso: nonce.issued_at,
        session_expires_at_iso,
      })

      const signDoc = buildAdr36SignDoc(address, message)

      let pubkey_b64: string
      let signature_b64: string

      if (kit.isConnected && kit.offlineSigner) {
        // Canonical path — InterwovenKit signs the ADR-36 doc on Initia.
        const signed = await kit.offlineSigner.signAmino(address, signDoc as never)
        pubkey_b64 = signed.signature.pub_key.value
        signature_b64 = signed.signature.signature
      } else if (fallback) {
        // Dev/test fallback — sign with localStorage secp256k1 wallet.
        const canonical = canonicalize(signDoc)
        const bytes = new TextEncoder().encode(canonical)
        const digest = sha256(bytes)
        const sig = secp256k1.sign(digest, fallback.priv).toCompactRawBytes()
        pubkey_b64 = b64encode(fallback.pub)
        signature_b64 = b64encode(sig)
      } else {
        throw new Error("no signer available")
      }

      const verify = await verifySignature({
        hubUrl: HUB_URL,
        address,
        chain: CHAIN,
        nonce: nonce.nonce,
        pubkey_b64,
        signature_b64,
        session_pub_b64: session.pub_b64,
        session_scope: SESSION_SCOPE,
        session_expires_at_iso,
      })

      const stored: StoredJwt = {
        access_token: verify.access_token,
        session_id: verify.session_id,
        session_priv_hex: hex(session.priv),
        address,
        init_username: verify.init_username,
        exp: jwtExpMs(verify.access_token) || Date.now() + 15 * 60 * 1000,
      }
      saveJwt(stored)
      setToken(stored)
      setStatus("ok")
    } catch (e: unknown) {
      setStatus("error")
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      inFlight.current = false
    }
  }, [activeAddress, kit, fallback])

  const signOut = useCallback(() => {
    clearJwt()
    setToken(null)
    setStatus("idle")
  }, [])

  return {
    token,
    status,
    error,
    hydrated,
    run,
    signOut,
    address: activeAddress,
    isInterwovenConnected: kit.isConnected,
    initUsername: token?.init_username ?? kit.username ?? null,
  }
}

// Recursively sort object keys, emit with separators=(",", ":") to match
// Python's json.dumps(sort_keys=True). Arrays are not reordered.
function canonicalize(v: unknown): string {
  if (v === null || typeof v !== "object") return JSON.stringify(v)
  if (Array.isArray(v)) return "[" + v.map(canonicalize).join(",") + "]"
  const keys = Object.keys(v as Record<string, unknown>).sort()
  return (
    "{" +
    keys
      .map((k) => JSON.stringify(k) + ":" + canonicalize((v as Record<string, unknown>)[k]))
      .join(",") +
    "}"
  )
}
