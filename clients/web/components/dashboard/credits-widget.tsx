"use client"

import Link from "next/link"
import { useState } from "react"
import { Wallet, Copy, Check } from "lucide-react"
import { useChainWallet } from "@/hooks/use-queries"
import { Skeleton } from "./skeleton"

type ToneKey = "halted" | "red" | "amber" | "green"

/**
 * Header chip: per-user 0G wallet balance + copy-address button.
 * Click body → /app/settings (wallet card lives there).
 */
export function CreditsWidget() {
  const { data, isLoading } = useChainWallet()
  const [copied, setCopied] = useState(false)

  if (isLoading) return <Skeleton className="w-32" height={28} />
  if (!data) return null

  const balance = Number(data.balance_og || 0)
  const threshold = Number(data.threshold_og || 0)
  const toneKey = balanceTone(balance, threshold)
  const t = TONE[toneKey]

  const copy = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!data.address) return
    await navigator.clipboard.writeText(data.address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs ${t.bg} ${t.text}`}
      title={data.address ? `${data.address} · ${balance.toFixed(4)} OG` : "no wallet"}
    >
      <Link
        href="/app/settings"
        className="focus-ring inline-flex items-center gap-1.5"
      >
        <Wallet size={12} />
        <span className="num-tabular font-mono font-semibold">
          {balance.toFixed(3)}
        </span>
        <span className="text-[10px] uppercase opacity-65">OG</span>
      </Link>
      <button
        onClick={copy}
        disabled={!data.address}
        className="focus-ring -mr-1 ml-0.5 inline-flex h-5 w-5 items-center justify-center rounded text-foreground/55 hover:bg-white/10 hover:text-foreground disabled:opacity-40"
        title={copied ? "Copied!" : "Copy wallet address"}
        aria-label="Copy wallet address"
      >
        {copied ? <Check size={11} className="text-[var(--color-teal)]" /> : <Copy size={11} />}
      </button>
    </div>
  )
}

const TONE: Record<ToneKey, { text: string; bg: string }> = {
  halted: { text: "text-foreground/60", bg: "bg-white/[0.05]" },
  red:    { text: "text-[var(--color-red-light)]", bg: "bg-[var(--color-red)]/12" },
  amber:  { text: "text-[var(--color-amber)]", bg: "bg-[var(--color-amber)]/12" },
  green:  { text: "text-[var(--color-teal)]", bg: "bg-[var(--color-teal)]/12" },
}

function balanceTone(balance: number, threshold: number): ToneKey {
  if (balance <= 0) return "halted"
  if (balance < threshold) return "red"
  if (balance < threshold * 5) return "amber"
  return "green"
}
