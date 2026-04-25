"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowRight, Check, Copy } from "lucide-react"
import { ConnectButton } from "@/components/wallet/connect-button"
import { useWallet } from "@/hooks/use-wallet"
import { useHubAuth } from "@/hooks/use-hub-auth"
import { displayName, shortenAddr } from "@/lib/identity"

export function ConnectWalletClient() {
  const { address: walletAddress, username, isConnected, openConnect } = useWallet()
  const { token, status, error, run, address: devAddress } = useHubAuth()

  const step = status === "ok" ? 2 : 1

  return (
    <div className="flex flex-col gap-6">
      <StepStatus step={step} />

      <div className="rounded-md border border-white/10 bg-white/[0.02] p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-foreground/50">
          Dev wallet (persisted in localStorage)
        </p>
        <code className="mt-1 block truncate font-mono text-xs text-foreground/80">
          {devAddress ?? "generating…"}
        </code>
      </div>

      {step === 1 && (
        <div className="flex flex-col gap-3">
          <button
            onClick={run}
            disabled={status === "running" || !devAddress}
            className="w-full rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-orange-text)] transition hover:bg-[var(--color-orange)]/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "running" ? "Signing…" : "Sign in to hub"}
          </button>
          {status === "error" && error && (
            <p className="rounded-md border border-[var(--color-red)]/30 bg-[var(--color-red)]/5 p-3 text-xs text-[var(--color-red-light)]">
              {error}
            </p>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="flex flex-col gap-3">
          <Link
            href="/app"
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-[var(--color-teal)]/40 bg-[var(--color-teal)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--color-teal)] transition hover:bg-[var(--color-teal)]/20"
          >
            Go to dashboard
            <ArrowRight size={16} />
          </Link>
          <JwtCopyRow token={token?.access_token ?? null} />
        </div>
      )}

      <div className="rounded-md border border-white/5 bg-white/[0.01] p-3 text-[11px] text-foreground/50">
        <p className="font-semibold text-foreground/70">Optional: connect an Initia wallet</p>
        <p className="mt-1">
          Future on-chain actions (funding, trades on real testnet) will use InterwovenKit. Hub
          auth keeps using the dev wallet above.
        </p>
        <div className="mt-3">
          {isConnected ? (
            <div className="flex items-center gap-3 font-mono">
              <span className="h-2 w-2 rounded-full bg-[var(--color-teal)]" />
              <span className="truncate text-foreground/70">
                {username
                  ? `${displayName(walletAddress, username)} · ${shortenAddr(walletAddress)}`
                  : shortenAddr(walletAddress)}
              </span>
              <div className="ml-auto">
                <ConnectButton />
              </div>
            </div>
          ) : (
            <button
              onClick={openConnect}
              className="rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-foreground/80 hover:text-foreground"
            >
              Connect Initia wallet
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function StepStatus({ step }: { step: 1 | 2 }) {
  const steps = [
    { n: 1, label: "Sign in to hub" },
    { n: 2, label: "Enter dashboard" },
  ]
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

function JwtCopyRow({ token }: { token: string | null }) {
  const [copied, setCopied] = useState(false)
  if (!token) return null
  const copy = async () => {
    await navigator.clipboard.writeText(token)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.02] p-3">
      <p className="text-[11px] font-semibold text-foreground/60">Hub JWT (Postman)</p>
      <div className="mt-2 flex items-start gap-2">
        <code className="flex-1 min-w-0 truncate rounded bg-black/40 px-2 py-1 font-mono text-[11px] text-foreground/80">
          {token}
        </code>
        <button
          onClick={copy}
          className="inline-flex items-center gap-1 rounded border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-foreground/70 hover:text-foreground"
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  )
}
