"use client"

import { useMemo } from "react"
import Link from "next/link"
import { ArrowDownRight, ArrowUpRight, Plus, TrendingUp } from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"
import { displayName } from "@/lib/identity"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { PnlChart } from "@/components/dashboard/pnl-chart"
import { AgentStatus, demoAgents, demoTrades } from "@/lib/demo-data"

const STATUS_TONE: Record<AgentStatus, string> = {
  alive: "text-[var(--color-teal)] bg-[var(--color-teal)]/10 border-[var(--color-teal)]/30",
  starting: "text-[var(--color-orange)] bg-[var(--color-orange)]/10 border-[var(--color-orange)]/30",
  stopped: "text-foreground/50 bg-white/[0.04] border-white/10",
  error: "text-[var(--color-red-light)] bg-[var(--color-red)]/10 border-[var(--color-red)]/30",
  halted: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
}

export default function AgentsPage() {
  const { address, username } = useWallet()

  const totals = useMemo(() => {
    const realisedByAgent: Record<string, number> = {}
    let realised = 0
    let tradeCount = 0
    let winCount = 0
    for (const t of demoTrades) {
      if (t.pnl == null) continue
      realised += t.pnl
      realisedByAgent[t.agent_id] = (realisedByAgent[t.agent_id] ?? 0) + t.pnl
      tradeCount += 1
      if (t.pnl > 0) winCount += 1
    }
    const unrealised = demoAgents.reduce(
      (sum, a) => sum + (a.unrealised_pnl ?? 0),
      0
    )
    return {
      realised,
      unrealised,
      total: realised + unrealised,
      tradeCount,
      winRate: tradeCount ? winCount / tradeCount : 0,
      realisedByAgent,
    }
  }, [])

  return (
    <div className="space-y-8">
      <PageHeader
        title="Your agents"
        subtitle={
          <>
            Signed in as <span className="text-foreground/80">{displayName(address, username)}</span>
          </>
        }
        action={
          <Link
            href="/app/agents/new"
            className="inline-flex items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] hover:bg-[var(--color-orange)]/20"
          >
            <Plus size={16} />
            New agent
          </Link>
        }
      />

      <PendingHub what="Agent list + trades come from GET /api/v1/u/agents and /u/agents/{id}/trades." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>
          {demoAgents.length} agents · {totals.tradeCount} closed trades in fixture set.
        </span>
      </div>

      {/* ── Stat strip ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat
          label="Total PnL"
          value={totals.total}
          emphasis
          hint={`${fmt(totals.realised)} realised ${fmt(totals.unrealised)} open`}
        />
        <Stat label="Realised" value={totals.realised} />
        <Stat label="Unrealised" value={totals.unrealised} />
        <StatPlain
          label="Win rate"
          value={`${(totals.winRate * 100).toFixed(0)}%`}
          hint={`${totals.tradeCount} closed`}
          icon={<TrendingUp size={15} className="text-[var(--color-orange)]" />}
        />
      </div>

      {/* ── PnL chart ─────────────────────────────────────────── */}
      <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
        <header className="mb-4 flex items-baseline justify-between">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Cumulative PnL</h3>
            <p className="mt-0.5 text-xs text-foreground/50">
              Realised PnL from closed trades, per agent. Zero line dashed.
            </p>
          </div>
          <span
            className={`font-mono text-base ${
              totals.realised > 0
                ? "text-[var(--color-teal)]"
                : totals.realised < 0
                  ? "text-[var(--color-red-light)]"
                  : "text-foreground/60"
            }`}
          >
            {fmt(totals.realised)} USDT
          </span>
        </header>
        <PnlChart agents={demoAgents} trades={demoTrades} height={320} />
      </section>

      {/* ── Agent grid ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {demoAgents.map((a) => {
          const unrealised = a.unrealised_pnl
          const realised = totals.realisedByAgent[a.id] ?? 0
          return (
            <Link
              key={a.id}
              href={`/app/agents/${a.id}`}
              className="group rounded-xl border border-white/10 bg-white/[0.02] p-5 transition hover:border-[var(--color-orange)]/40"
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-foreground">{a.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-foreground/50">{a.symbol}</p>
                </div>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${STATUS_TONE[a.status]}`}
                >
                  {a.status}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <Kv label="Price" value={a.price.toLocaleString()} />
                <Kv
                  label="Side"
                  value={
                    a.side === "flat" ? (
                      <span className="text-foreground/40">flat</span>
                    ) : a.side === "long" ? (
                      <span className="text-[var(--color-teal)]">long</span>
                    ) : (
                      <span className="text-[var(--color-red-light)]">short</span>
                    )
                  }
                />
                <Kv label="Realised" value={<Pnl value={realised} />} />
                <Kv
                  label="Unrealised"
                  value={unrealised == null ? <span className="text-foreground/40">—</span> : <Pnl value={unrealised} />}
                />
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-[11px] text-foreground/40">
                <span className="font-mono">{a.strategy}</span>
                <span>
                  {a.amount_usdt} USDT · {a.leverage}×
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ── Small primitives ────────────────────────────────────────────────────────

function Stat({
  label,
  value,
  hint,
  emphasis,
}: {
  label: string
  value: number
  hint?: string
  emphasis?: boolean
}) {
  const tone =
    value > 0
      ? "text-[var(--color-teal)]"
      : value < 0
        ? "text-[var(--color-red-light)]"
        : "text-foreground/70"
  const Icon = value >= 0 ? ArrowUpRight : ArrowDownRight
  return (
    <div
      className={`rounded-xl border bg-white/[0.02] p-4 ${
        emphasis ? "border-[var(--color-orange)]/25" : "border-white/10"
      }`}
    >
      <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-foreground/50">
        <span>{label}</span>
        <Icon size={12} className={tone} />
      </div>
      <p className={`mt-2 font-mono text-2xl font-semibold ${tone}`}>{fmt(value)}</p>
      <p className="mt-1 text-[11px] text-foreground/40">{hint ?? "USDT"}</p>
    </div>
  )
}

function StatPlain({
  label,
  value,
  hint,
  icon,
}: {
  label: string
  value: string
  hint?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-foreground/50">
        <span>{label}</span>
        {icon}
      </div>
      <p className="mt-2 font-mono text-2xl font-semibold text-foreground/90">{value}</p>
      {hint && <p className="mt-1 text-[11px] text-foreground/40">{hint}</p>}
    </div>
  )
}

function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-foreground/40">{label}</span>
      <span className="text-sm text-foreground/80">{value}</span>
    </div>
  )
}

function Pnl({ value }: { value: number }) {
  if (value === 0) return <span className="text-foreground/40">0.00</span>
  if (value > 0) return <span className="text-[var(--color-teal)]">+{value.toFixed(2)}</span>
  return <span className="text-[var(--color-red-light)]">{value.toFixed(2)}</span>
}

function fmt(v: number) {
  const abs = Math.abs(v)
  const sign = v > 0 ? "+" : v < 0 ? "-" : ""
  return `${sign}${abs.toFixed(2)}`
}
