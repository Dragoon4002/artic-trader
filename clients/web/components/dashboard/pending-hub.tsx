"use client"

import { AlertTriangle } from "lucide-react"

/**
 * Banner shown on any page that would otherwise fetch from the hub. Removed
 * once the /auth/verify round-trip + JWT storage + signedFetch are wired.
 */
export function PendingHub({ what }: { what: string }) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-[var(--color-orange)]/20 bg-[var(--color-orange)]/5 p-4 text-xs text-[var(--color-orange-text)]">
      <AlertTriangle size={16} className="mt-0.5 shrink-0 text-[var(--color-orange)]" />
      <div>
        <p className="font-semibold text-foreground/90">Pending hub session</p>
        <p className="mt-1 leading-relaxed">
          {what} Wallet is wired; next step is the{" "}
          <code className="rounded bg-white/[0.04] px-1 py-0.5 font-mono">/auth/verify</code> handshake
          that mints a JWT + session key.
        </p>
      </div>
    </div>
  )
}
