"use client"

import Link from "next/link"
import { Coins } from "lucide-react"
import { useCredits } from "@/hooks/use-queries"
import { Skeleton } from "./skeleton"

type ToneKey = "halted" | "red" | "amber" | "green"

/**
 * Balance chip rendered in the dashboard header. Colour state per alpha spec:
 * green > 10, amber 1-10, red < 1, grey halted.
 */
export function CreditsWidget() {
  const { data, isLoading } = useCredits()

  if (isLoading) return <Skeleton className="w-24" height={28} />

  const balance = data?.balance_ah ?? 0
  const toneKey = balanceTone(balance)
  const t = TONE[toneKey]

  return (
    <Link
      href="/app/credits"
      className={`focus-ring inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition ${t.bg} ${t.text} hover:opacity-90`}
      title={`${balance.toFixed(3)} agent-hours · ${toneKey}`}
    >
      <Coins size={12} />
      <span className="num-tabular font-mono font-semibold">
        {balance.toFixed(1)}
      </span>
      <span className="text-[10px] uppercase opacity-65">AH</span>
    </Link>
  )
}

const TONE: Record<ToneKey, { text: string; bg: string }> = {
  halted: {
    text: "text-foreground/60",
    bg: "bg-white/[0.05]",
  },
  red: {
    text: "text-[var(--color-red-light)]",
    bg: "bg-[var(--color-red)]/12",
  },
  amber: {
    text: "text-[var(--color-amber)]",
    bg: "bg-[var(--color-amber)]/12",
  },
  green: {
    text: "text-[var(--color-teal)]",
    bg: "bg-[var(--color-teal)]/12",
  },
}

function balanceTone(balance: number): ToneKey {
  if (balance <= 0) return "halted"
  if (balance < 1) return "red"
  if (balance <= 10) return "amber"
  return "green"
}
