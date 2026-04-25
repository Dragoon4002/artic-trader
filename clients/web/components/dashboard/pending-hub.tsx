"use client"

import { AlertTriangle } from "lucide-react"
import { useWarningsVisible } from "./warnings-context"

/**
 * Banner shown on any page that would otherwise fetch from the hub. Hidden
 * globally unless the user flips the navbar Warnings toggle on. Remove the
 * call sites entirely once /auth/verify + signedFetch are wired.
 */
export function PendingHub({ what }: { what: string }) {
  const visible = useWarningsVisible()
  if (!visible) return null
  return (
    <div className="flex items-start gap-3 rounded-xl bg-[var(--color-accent-warm-soft)] p-4 text-xs text-[var(--color-accent-warm)]">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
      <div>
        <p className="font-semibold text-foreground/90">Pending hub session</p>
        <p className="mt-1 leading-relaxed text-foreground/70">
          {what} Wallet is wired; next step is the{" "}
          <code className="rounded bg-white/[0.05] px-1 py-0.5 font-mono">
            /auth/verify
          </code>{" "}
          handshake that mints a JWT + session key.
        </p>
      </div>
    </div>
  )
}
