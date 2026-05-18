"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowRight, Check } from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"
import { useHubAuth } from "@/hooks/use-hub-auth"
import { useInjectedProviders } from "@/hooks/use-injected-providers"
import { shortenAddr } from "@/lib/identity"

export function ConnectWalletClient() {
  const { address, isConnected, openConnect, disconnect, revokeSupported } = useWallet()
  const { status, error, run, signOut } = useHubAuth()
  const providers = useInjectedProviders()
  const [showPicker, setShowPicker] = useState(false)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pickAndConnect = async (provider: any) => {
    signOut()
    await disconnect()
    await openConnect(provider)
    setShowPicker(false)
  }

  const switchWallet = async () => {
    if (providers.length > 1) {
      signOut()
      await disconnect()
      setShowPicker(true)
      return
    }
    signOut()
    await disconnect()
    await openConnect()
  }

  const step: 1 | 2 | 3 = !isConnected ? 1 : status === "ok" ? 3 : 2

  return (
    <div className="flex flex-col gap-6">
      <Stepper step={step} />

      <div className="rounded-md border border-white/10 bg-white/[0.02] p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-foreground/50">
          EVM wallet (0G mainnet)
        </p>
        <code className="mt-1 block truncate font-mono text-xs text-foreground/80">
          {address ?? "not connected"}
        </code>
      </div>

      {revokeSupported === false && isConnected && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-[11px] text-amber-200/80">
          <p className="font-semibold text-amber-200">Switch account in your wallet extension</p>
          <p className="mt-1">
            Your wallet does not support programmatic account switching. To use a
            different account: open your wallet extension popup, switch the active
            account there, then reload this page.{" "}
            <strong>MetaMask</strong> supports automatic switching.
          </p>
        </div>
      )}

      {step === 1 && !showPicker && (
        <div className="flex flex-col gap-2">
          {providers.length > 1 ? (
            providers.map((p) => (
              <WalletButton key={p.info.uuid} info={p.info} onClick={() => pickAndConnect(p.provider)} />
            ))
          ) : (
            <button
              onClick={() => openConnect()}
              className="w-full rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-orange-text)] transition hover:bg-[var(--color-orange)]/20"
            >
              Connect EVM wallet
            </button>
          )}
        </div>
      )}

      {showPicker && (
        <div className="flex flex-col gap-2">
          <p className="text-[11px] uppercase tracking-wide text-foreground/50">
            Choose a wallet
          </p>
          {providers.map((p) => (
            <WalletButton key={p.info.uuid} info={p.info} onClick={() => pickAndConnect(p.provider)} />
          ))}
          <button
            onClick={() => setShowPicker(false)}
            className="rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-foreground/70 hover:text-foreground"
          >
            Cancel
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="flex flex-col gap-3">
          <button
            onClick={run}
            disabled={status === "running"}
            className="w-full rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-orange-text)] transition hover:bg-[var(--color-orange)]/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "running" ? "Signing…" : "Sign in to hub (SIWE)"}
          </button>
          {status === "error" && error && (
            <p className="rounded-md border border-[var(--color-red)]/30 bg-[var(--color-red)]/5 p-3 text-xs text-[var(--color-red-light)]">
              {error}
            </p>
          )}
          <button
            onClick={switchWallet}
            className="rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-foreground/70 hover:text-foreground"
          >
            Use a different wallet
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="flex flex-col gap-3">
          <Link
            href="/app"
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-[var(--color-teal)]/40 bg-[var(--color-teal)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-teal)] transition hover:bg-[var(--color-teal)]/20"
          >
            Go to dashboard
            <ArrowRight size={16} />
          </Link>
          <p className="text-center text-[11px] text-foreground/50">
            Signed in as <span className="font-mono">{shortenAddr(address)}</span>
          </p>
          <div className="flex gap-2">
            <button
              onClick={signOut}
              className="flex-1 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-foreground/70 hover:text-foreground"
            >
              Sign out
            </button>
            <button
              onClick={switchWallet}
              className="flex-1 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-foreground/70 hover:text-foreground"
            >
              Switch wallet
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function WalletButton({
  info,
  onClick,
}: {
  info: { name: string; icon: string; rdns: string }
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm text-foreground/90 hover:border-[var(--color-orange)]/40 hover:bg-white/[0.06]"
    >
      {info.icon ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={info.icon} alt={info.name} className="h-6 w-6 rounded" />
      ) : (
        <span className="h-6 w-6 rounded bg-white/10" />
      )}
      <span className="flex-1 text-left font-semibold">{info.name}</span>
      <span className="text-[10px] font-mono text-foreground/40">{info.rdns}</span>
    </button>
  )
}

function Stepper({ step }: { step: 1 | 2 | 3 }) {
  const steps = [
    { n: 1, label: "Connect wallet" },
    { n: 2, label: "Sign in" },
    { n: 3, label: "Enter dashboard" },
  ] as const
  return (
    <ol className="flex items-center gap-2 text-[11px] text-foreground/60">
      {steps.map((s, i) => {
        const done = step > s.n
        const active = step === s.n
        return (
          <li key={s.n} className="flex items-center gap-2">
            <span
              className={`flex h-5 w-5 items-center justify-center rounded-full font-mono text-[10px] ${
                done
                  ? "bg-[var(--color-teal)]/20 text-[var(--color-teal)]"
                  : active
                    ? "bg-[var(--color-orange)]/20 text-[var(--color-orange-text)]"
                    : "bg-white/5 text-foreground/40"
              }`}
            >
              {done ? <Check size={11} /> : s.n}
            </span>
            <span className={active ? "text-foreground" : ""}>{s.label}</span>
            {i < steps.length - 1 && <span className="text-foreground/20">—</span>}
          </li>
        )
      })}
    </ol>
  )
}

