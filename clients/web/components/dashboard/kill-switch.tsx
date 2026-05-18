"use client"

import { useState } from "react"
import { Play, Square, AlertTriangle } from "lucide-react"
import { useStartAllAgents, useStopAllAgents } from "@/hooks/use-queries"

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
  const [error, setError] = useState<string | null>(null)
  const startAllMut = useStartAllAgents()
  const stopAllMut = useStopAllAgents()

  if (totalCount === 0) return null

  const canStart = aliveCount < totalCount - haltedCount
  const canStop = aliveCount > 0

  const onConfirmStart = async () => {
    setError(null)
    try {
      await startAllMut.mutateAsync()
      setConfirming(null)
    } catch (e) {
      setError(String((e as Error)?.message ?? e))
    }
  }

  const onConfirmStop = async () => {
    setError(null)
    try {
      await stopAllMut.mutateAsync()
      setConfirming(null)
    } catch (e) {
      setError(String((e as Error)?.message ?? e))
    }
  }

  if (confirming === "stop") {
    return (
      <ConfirmBar
        tone="danger"
        message={`Stop all ${aliveCount} alive agent${aliveCount === 1 ? "" : "s"}?`}
        busy={stopAllMut.isPending}
        error={error}
        onConfirm={onConfirmStop}
        onCancel={() => { setError(null); setConfirming(null) }}
      />
    )
  }
  if (confirming === "start") {
    return (
      <ConfirmBar
        tone="warn"
        message="Start every stopped agent?"
        busy={startAllMut.isPending}
        error={error}
        onConfirm={onConfirmStart}
        onCancel={() => { setError(null); setConfirming(null) }}
      />
    )
  }

  return (
    <div className="inline-flex items-center gap-2">
      <button
        disabled={!canStart}
        title={!canStart ? "Nothing to start" : "Start every stopped agent"}
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
  busy,
  error,
  onConfirm,
  onCancel,
}: {
  tone: "danger" | "warn"
  message: string
  busy: boolean
  error: string | null
  onConfirm: () => void
  onCancel: () => void
}) {
  const accent =
    tone === "danger"
      ? "bg-[var(--color-red)]/12 text-[var(--color-red-light)]"
      : "bg-[var(--color-amber)]/12 text-[var(--color-amber)]"
  return (
    <div className="inline-flex flex-col gap-1">
      <div className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs ${accent}`}>
        <AlertTriangle size={12} />
        <span className="font-semibold">{message}</span>
        <button
          onClick={onCancel}
          disabled={busy}
          className="focus-ring rounded bg-white/[0.06] px-2 py-0.5 text-[11px] text-foreground/80 transition hover:bg-white/[0.1] hover:text-foreground disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={busy}
          className="focus-ring rounded bg-white/15 px-2 py-0.5 text-[11px] font-semibold text-foreground/90 transition hover:bg-white/25 disabled:opacity-50"
        >
          {busy ? "Working…" : "Confirm"}
        </button>
      </div>
      {error && (
        <p className="text-[10px] text-[var(--color-red-light)]">Error: {error}</p>
      )}
    </div>
  )
}
