"use client"

import { Copy, LogOut } from "lucide-react"
import { useState } from "react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { ChainWalletCard } from "@/components/wallet/chain-wallet-card"
import { useWallet } from "@/hooks/use-wallet"
import { displayName, shortenAddr } from "@/lib/identity"
import { CHAIN_ID, EVM_CHAIN_ID } from "@/lib/chain"

export default function SettingsPage() {
  const { address, username, disconnect } = useWallet()
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    if (!address) return
    await navigator.clipboard.writeText(address)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-8">
      <PageHeader title="Settings" subtitle="Your identity and wallet." />

      <Section title="Identity">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">{displayName(address, username)}</p>
            <p className="mt-0.5 font-mono text-xs text-foreground/50">{shortenAddr(address)}</p>
            <p className="mt-2 font-mono text-[11px] text-foreground/40">
              Chain: <span className="text-foreground/60">{CHAIN_ID}</span>
              <span className="mx-1.5 text-foreground/20">·</span>
              EVM: <span className="text-foreground/60">{EVM_CHAIN_ID}</span>
            </p>
          </div>
          <button
            onClick={copy}
            className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-foreground/70 hover:text-foreground"
          >
            <Copy size={12} />
            {copied ? "Copied" : "Copy address"}
          </button>
        </div>
      </Section>

      <ChainWalletCard />

      <Section title="Session">
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground/60">
            Disconnect clears the wallet session in this tab and sends you to{" "}
            <code className="font-mono text-xs">/connect</code>.
          </p>
          <button
            onClick={() => {
              disconnect()
              if (typeof window !== "undefined") window.location.href = "/connect"
            }}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--color-red)]/30 bg-white/[0.02] px-3 py-1.5 text-xs font-semibold text-[var(--color-red-light)] hover:bg-[var(--color-red)]/10"
          >
            <LogOut size={12} /> Disconnect
          </button>
        </div>
      </Section>
    </div>
  )
}

function Section({
  title,
  right,
  children,
}: {
  title: string
  right?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-foreground/50">{title}</h3>
        {right}
      </div>
      {children}
    </section>
  )
}

