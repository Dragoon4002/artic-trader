"use client"

import { PropsWithChildren, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useWallet } from "@/hooks/use-wallet"

/**
 * Client-side redirect to /connect when no wallet is connected. InterwovenKit
 * state only exists in the browser, so this can't be a middleware guard.
 * Renders nothing while unverified to avoid a flicker.
 */
export function AuthGuard({ children }: PropsWithChildren) {
  const router = useRouter()
  const { isConnected } = useWallet()

  useEffect(() => {
    if (!isConnected) router.replace("/connect")
  }, [isConnected, router])

  if (!isConnected) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-foreground/50">
        Redirecting…
      </div>
    )
  }

  return <>{children}</>
}
