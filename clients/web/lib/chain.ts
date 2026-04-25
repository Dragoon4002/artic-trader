export const CHAIN_ID = "initiation-2"
export const RPC_URL = "https://rpc.testnet.initia.xyz"
export const LCD_URL = "https://rest.testnet.initia.xyz"
export const AUTH_CHAIN_NAME = "initia-testnet"

// Rollup chain ID (your own appchain). Override via NEXT_PUBLIC_INITIA_ROLLUP_CHAIN_ID
// once `weave init` returns the chosen ID.
export const ROLLUP_CHAIN_ID =
  (process.env.NEXT_PUBLIC_INITIA_ROLLUP_CHAIN_ID as string | undefined) || "artic-1"

const EXPLORER_BASE =
  (process.env.NEXT_PUBLIC_INITIA_EXPLORER_BASE as string | undefined) ||
  "https://scan.testnet.initia.xyz"

/** Build an explorer URL for a tx hash on the rollup. */
export function explorerTxUrl(txHash: string | null | undefined): string | null {
  if (!txHash) return null
  const h = txHash.startsWith("0x") ? txHash : `0x${txHash}`
  return `${EXPLORER_BASE.replace(/\/+$/, "")}/${ROLLUP_CHAIN_ID}/tx/${h}`
}

/** Short hash like 0x1a2b…f8e9 for inline display. */
export function shortHash(txHash: string | null | undefined): string {
  if (!txHash) return ""
  const h = txHash.startsWith("0x") ? txHash : `0x${txHash}`
  if (h.length <= 12) return h
  return `${h.slice(0, 6)}…${h.slice(-4)}`
}
