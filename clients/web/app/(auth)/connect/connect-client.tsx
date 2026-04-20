"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowRight, CheckCircle2 } from "lucide-react"
import { ConnectButton } from "@/components/wallet/connect-button"
import { useWallet } from "@/hooks/use-wallet"
import { displayName, shortenAddr } from "@/lib/identity"

export function ConnectWalletClient() {
  const { address, username, isConnected, autoSign } = useWallet()
  const router = useRouter()

  useEffect(() => {
    // Seamless bounce to dashboard on connect. Users can still land here
    // manually; the CTA below provides an explicit entry.
    if (isConnected) {
      const t = setTimeout(() => router.replace("/app"), 400)
      return () => clearTimeout(t)
    }
  }, [isConnected, router])

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center gap-6">
        <ConnectButton />
        <p className="text-center text-xs text-foreground/50">
          New to Initia? InterwovenKit supports any Cosmos wallet as well as email / social login via
          Privy.
        </p>
      </div>
    )
  }

  const isAutoSignEnabled =
    autoSign?.isEnabledByChain && Object.values(autoSign.isEnabledByChain).some(Boolean)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3 rounded-md border border-[var(--color-teal)]/30 bg-[var(--color-teal)]/5 p-4">
        <CheckCircle2 size={22} className="text-[var(--color-teal)]" />
        <div>
          <p className="text-sm font-semibold text-foreground">Wallet connected</p>
          <p className="mt-0.5 truncate font-mono text-xs text-foreground/50">
            {username ? `${displayName(address, username)} · ${shortenAddr(address)}` : shortenAddr(address)}
          </p>
        </div>
      </div>

      <div className="rounded-md border border-white/10 bg-white/[0.02] p-4 text-xs text-foreground/60">
        <p className="font-semibold text-foreground/80">Auto-signing session</p>
        <p className="mt-1">
          {isAutoSignEnabled
            ? "Active — dashboard actions will submit without a wallet popup until the session expires."
            : "Open Wallet Manager and enable Auto-Sign to skip wallet popups on dashboard actions."}
        </p>
      </div>

      <Link
        href="/app"
        className="inline-flex items-center justify-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-orange-text)] transition hover:bg-[var(--color-orange)]/20 hover:border-[var(--color-orange)]/70"
      >
        Enter dashboard
        <ArrowRight size={16} />
      </Link>

      <div className="flex justify-center">
        <ConnectButton />
      </div>

      <p className="text-center text-xs text-foreground/40">
        Auto-redirecting to the dashboard… click above if nothing happens.
      </p>
    </div>
  )
}
