"use client"

import { useState } from "react"
import { Play, Square, AlertTriangle } from "lucide-react"

/**
 * Group toolbar for /app/agents. Start-all + Stop-all with an explicit
 * confirm step. Wiring points to signed POST /u/agents/{start,stop}-all once
 * hub auth lands — currently the buttons are disabled with hover hints.
 */
export function KillSwitch({
  aliveCount,
  haltedCount,
  totalCount,
}: {
  aliveCount: number
  haltedCount: number
  totalCount: number
}) {
  const [confirming, setConfirming] = useState<"start" | "stop" | null>(null)

  if (totalCount === 0) return null

  const canStart = aliveCount < totalCount - haltedCount
  const canStop = aliveCount > 0

  if (confirming === "stop") {
    return (
      <ConfirmBar
        tone="danger"
        message={`Stop all ${aliveCount} alive agent${aliveCount === 1 ? "" : "s"}?`}
        onConfirm={() => setConfirming(null)}
        onCancel={() => setConfirming(null)}
      />
    )
  }
  if (confirming === "start") {
    return (
      <ConfirmBar
        tone="warn"
        message="Start every stopped agent?"
        onConfirm={() => setConfirming(null)}
        onCancel={() => setConfirming(null)}
      />
    )
  }

  return (
    <div className="inline-flex items-center gap-2">
      <button
        disabled={!canStart}
        title={!canStart ? "Nothing to start" : "Hub auth wiring pending"}
        onClick={() => setConfirming("start")}
        className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-white/[0.04] px-5 py-3 text-sm font-semibold text-foreground/80 transition hover:bg-white/[0.08] hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Play size={12} /> Start all
      </button>
      <button
        disabled={!canStop}
        title={!canStop ? "No alive agents" : "Kill switch"}
        onClick={() => setConfirming("stop")}
        className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-[var(--color-red)]/10 px-5 py-3 text-sm font-semibold text-[var(--color-red-light)] transition hover:bg-[var(--color-red)]/18 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Square size={12} /> Stop all
      </button>
    </div>
  )
}

function ConfirmBar({
  tone,
  message,
  onConfirm,
  onCancel,
}: {
  tone: "danger" | "warn"
  message: string
  onConfirm: () => void
  onCancel: () => void
}) {
  const accent =
    tone === "danger"
      ? "bg-[var(--color-red)]/12 text-[var(--color-red-light)]"
      : "bg-[var(--color-amber)]/12 text-[var(--color-amber)]"
  return (
    <div
      className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs ${accent}`}
    >
      <AlertTriangle size={12} />
      <span className="font-semibold">{message}</span>
      <button
        onClick={onCancel}
        className="focus-ring rounded bg-white/[0.06] px-2 py-0.5 text-[11px] text-foreground/80 transition hover:bg-white/[0.1] hover:text-foreground"
      >
        Cancel
      </button>
      <button
        disabled
        title="Hub auth wiring pending"
        onClick={onConfirm}
        className="btn-disabled rounded bg-white/10 px-2 py-0.5 text-[11px] font-semibold text-foreground/70"
      >
        Confirm
      </button>
    </div>
  )
}
