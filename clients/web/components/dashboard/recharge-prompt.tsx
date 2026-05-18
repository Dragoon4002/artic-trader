"use client"

import Link from "next/link"
import { useState } from "react"
import { AlertTriangle, X, Copy, Check, ArrowUpRight } from "lucide-react"
import { useChainWallet } from "@/hooks/use-queries"

const LOW_GAS_THRESHOLD_OG = 0.5

export function RechargePrompt() {
  const { data, isLoading } = useChainWallet()
  const [dismissed, setDismissed] = useState(false)
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  if (isLoading || !data || dismissed) return null

  const balance = Number(data.balance_og || 0)
  if (balance >= LOW_GAS_THRESHOLD_OG) return null

  const copy = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!data.address) return
    await navigator.clipboard.writeText(data.address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const short = data.address
    ? `${data.address.slice(0, 6)}…${data.address.slice(-4)}`
    : "no wallet"

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-[var(--color-red)]/12 px-2.5 py-1.5 text-xs text-[var(--color-red-light)] hover:bg-[var(--color-red)]/18"
        title="Low gas — recharge required"
      >
        <AlertTriangle size={12} />
        <span className="font-semibold">Low gas</span>
        <span className="text-[10px] uppercase opacity-65">recharge</span>
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            role="presentation"
          />
          <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-80 rounded-xl border border-[rgba(228,71,59,0.25)] bg-[var(--color-surface-raised)] p-4 shadow-2xl">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertTriangle size={14} className="text-[var(--color-red-light)]" />
                <h3 className="text-sm font-semibold text-foreground">
                  Gas balance low
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setDismissed(true)}
                className="focus-ring -mt-1 -mr-1 inline-flex h-6 w-6 items-center justify-center rounded text-foreground/55 hover:bg-white/10 hover:text-foreground"
                title="Hide for this session"
                aria-label="Dismiss"
              >
                <X size={12} />
              </button>
            </div>

            <p className="mt-2 text-xs leading-relaxed text-foreground/65">
              Wallet has{" "}
              <span className="font-mono font-semibold text-[var(--color-red-light)]">
                {balance.toFixed(4)} OG
              </span>
              . Agents need on-chain gas to log trades + decisions. Send OG to
              the address below to keep them running.
            </p>

            <div className="mt-3 rounded-lg bg-white/[0.04] p-2.5">
              <div className="text-[10px] uppercase tracking-wide text-foreground/45">
                Your 0G wallet
              </div>
              <div className="mt-1 flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-foreground/85">
                  {short}
                </span>
                <button
                  type="button"
                  onClick={copy}
                  disabled={!data.address}
                  className="focus-ring inline-flex h-6 w-6 items-center justify-center rounded text-foreground/55 hover:bg-white/10 hover:text-foreground disabled:opacity-40"
                  title={copied ? "Copied!" : "Copy address"}
                  aria-label="Copy wallet address"
                >
                  {copied ? (
                    <Check size={11} className="text-[var(--color-teal)]" />
                  ) : (
                    <Copy size={11} />
                  )}
                </button>
              </div>
            </div>

            <Link
              href="/app/settings"
              onClick={() => setOpen(false)}
              className="focus-ring mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-[var(--color-accent-warm)] px-3 py-2 text-xs font-semibold text-black hover:opacity-90"
            >
              Open wallet settings
              <ArrowUpRight size={12} />
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
