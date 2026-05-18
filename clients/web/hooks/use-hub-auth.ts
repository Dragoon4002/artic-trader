"use client"

/**
 * Hub auth via EIP-4361 (SIWE) on 0G mainnet.
 *
 * Flow:
 *   1. user connects an injected EVM wallet via useWallet() (EIP-6963 picker)
 *   2. fetch nonce from hub keyed on wallet address
 *   3. wagmi.useSignMessage personal_signs the canonical sign-in message —
 *      routes through the connector wagmi already bound to, so multi-wallet
 *      setups never hit the wrong injected provider
 *   4. POST signature to /auth/verify → JWT
 */

import { useCallback, useEffect, useRef, useState } from "react"
import { useSignMessage, useSwitchChain, useChainId } from "wagmi"
import {
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
import { useWallet } from "@/hooks/use-wallet"

const HUB_URL =
  (process.env.NEXT_PUBLIC_HUB_URL as string | undefined) || "http://localhost:9000"
const CHAIN =
  (process.env.NEXT_PUBLIC_HUB_AUTH_EVM_CHAIN as string | undefined) || "0g-mainnet"
const SESSION_SCOPE = "authenticated-actions"
const SESSION_TTL_SECONDS = 8 * 60 * 60

type Status = "idle" | "running" | "ok" | "error"

const TARGET_CHAIN_ID = Number(
  (process.env.NEXT_PUBLIC_ZERO_G_CHAIN_ID as string | undefined) || "16661",
)

export function useHubAuth() {
  const { address: walletAddress, isConnected, openConnect } = useWallet()
  const { signMessageAsync } = useSignMessage()
  const { switchChainAsync } = useSwitchChain()
  const currentChainId = useChainId()
  const [token, setToken] = useState<StoredJwt | null>(null)
  const [status, setStatus] = useState<Status>("idle")
  const [error, setError] = useState<string | null>(null)
  const [hydrated, setHydrated] = useState(false)
  const inFlight = useRef(false)

  useEffect(() => {
    const cached = loadJwt()
    if (cached && cached.exp > Date.now()) {
      setToken(cached)
      setStatus("ok")
    }
    setHydrated(true)
  }, [])

  const run = useCallback(async () => {
    if (inFlight.current) return
    if (!walletAddress || !isConnected) {
      setError("connect a wallet first")
      setStatus("error")
      return
    }
    inFlight.current = true
    setStatus("running")
    setError(null)
    try {
      const address = walletAddress

      // Read the wallet's ACTUAL chain — wagmi's useChainId returns the
      // wagmi-configured chain, not what the wallet is currently pointing at.
      let walletChainHex = ""
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const eth = (typeof window !== "undefined" ? (window as any).ethereum : null)
      if (eth?.request) {
        try {
          walletChainHex = (await eth.request({ method: "eth_chainId" })) as string
        } catch (e) {
          console.warn("[hub-auth] eth_chainId failed:", e)
        }
      }
      const walletChainId = walletChainHex ? parseInt(walletChainHex, 16) : currentChainId
      console.log(
        "[hub-auth] chain check wallet=%s wagmi=%s target=%s",
        walletChainId,
        currentChainId,
        TARGET_CHAIN_ID,
      )

      if (walletChainId !== TARGET_CHAIN_ID) {
        const targetHex = "0x" + TARGET_CHAIN_ID.toString(16)
        console.log("[hub-auth] switching wallet to", targetHex)
        try {
          // wagmi switchChain first (uses connector-aware path)
          await switchChainAsync({ chainId: TARGET_CHAIN_ID })
        } catch {
          // Fallback: raw EIP-3326 + EIP-3085 to inject chain if unknown
          if (eth?.request) {
            try {
              await eth.request({
                method: "wallet_switchEthereumChain",
                params: [{ chainId: targetHex }],
              })
            } catch (switchErr) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              if ((switchErr as any)?.code === 4902 || /unrecognized/i.test(String(switchErr))) {
                await eth.request({
                  method: "wallet_addEthereumChain",
                  params: [
                    {
                      chainId: targetHex,
                      chainName: "0G Mainnet",
                      nativeCurrency: { name: "0G", symbol: "0G", decimals: 18 },
                      rpcUrls: ["https://evmrpc.0g.ai"],
                      blockExplorerUrls: ["https://chainscan.0g.ai"],
                    },
                  ],
                })
              } else {
                throw switchErr
              }
            }
          }
        }
        // Verify
        const newHex = (await eth.request({ method: "eth_chainId" })) as string
        if (parseInt(newHex, 16) !== TARGET_CHAIN_ID) {
          throw new Error("wallet did not switch to 0G Mainnet — switch manually and retry")
        }
        console.log("[hub-auth] switched ok")
      }

      let nonce: Awaited<ReturnType<typeof fetchNonce>>
      try {
        nonce = await fetchNonce(HUB_URL, address, CHAIN)
      } catch (e) {
        throw new Error(`nonce fetch failed: ${(e as Error).message}`)
      }

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

      let sig: string
      try {
        sig = await signMessageAsync({
          message,
          account: address as `0x${string}`,
        })
      } catch (e) {
        throw new Error(`sign failed: ${(e as Error).message}`)
      }

      const verify = await verifySignature({
        hubUrl: HUB_URL,
        address,
        chain: CHAIN,
        nonce: nonce.nonce,
        pubkey_b64: "",
        signature_b64: sig,
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
      console.error("[hub-auth] run failed:", e)
      setStatus("error")
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      inFlight.current = false
    }
  }, [walletAddress, isConnected, signMessageAsync, currentChainId, switchChainAsync])

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
    openConnect,
    address: walletAddress,
    isWalletConnected: isConnected,
    initUsername: token?.init_username ?? null,
  }
}
