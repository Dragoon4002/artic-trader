"use client"

import { useInterwovenKit } from "@initia/interwovenkit-react"

/**
 * Thin ergonomic wrapper over useInterwovenKit. Returns only what dashboard
 * components care about. Tx-submission helpers are passed through untouched.
 */
export function useWallet() {
  const kit = useInterwovenKit()
  return {
    address: kit.address ?? null,
    username: kit.username ?? null,
    isConnected: kit.isConnected ?? false,
    openConnect: kit.openConnect,
    openWallet: kit.openWallet,
    disconnect: kit.disconnect,
    autoSign: kit.autoSign,
    requestTxBlock: kit.requestTxBlock,
    submitTxBlock: kit.submitTxBlock,
    estimateGas: kit.estimateGas,
  }
}
