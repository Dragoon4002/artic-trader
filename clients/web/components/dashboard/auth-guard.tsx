"use client"

import { PropsWithChildren, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useHubAuth } from "@/hooks/use-hub-auth"

/**
 * Redirect to /connect when there's no hub-auth JWT. InterwovenKit wallet is
 * optional; the actual gate is the JWT in localStorage.
 */
export function AuthGuard({ children }: PropsWithChildren) {
  const router = useRouter()
  const { token, hydrated } = useHubAuth()

  useEffect(() => {
    if (hydrated && !token) router.replace("/connect")
  }, [hydrated, token, router])

  if (!hydrated || !token) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-foreground/50">
        Redirecting…
      </div>
    )
  }

  return <>{children}</>
}
