"use client"

import { useMemo } from "react"
import Link from "next/link"
import {
  ArrowDownRight,
  ArrowUpRight,
  Inbox,
  Plus,
  Target,
  TrendingUp,
} from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"
import { useAgents, useTrades } from "@/hooks/use-queries"
import { displayName } from "@/lib/identity"
import { EmptyState, PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { PnlChart, PnlChartCard } from "@/components/dashboard/pnl-chart"
import { Skeleton } from "@/components/dashboard/skeleton"
import { KillSwitch } from "@/components/dashboard/kill-switch"
import type { Agent, AgentStatusT } from "@/lib/schemas"
import type { DemoTrade } from "@/lib/demo-data"
import { fmtInit, usdToInit } from "@/lib/currency"

const STATUS_TONE: Record<AgentStatusT, string> = {
  alive: "text-[var(--color-teal)] bg-[var(--color-teal)]/12",
  starting: "text-[var(--color-accent-warm)] bg-[var(--color-accent-warm-soft)]",
  stopped: "text-foreground/55 bg-white/[0.05]",
  error: "text-[var(--color-red-light)] bg-[var(--color-red)]/12",
  halted: "text-[var(--color-amber)] bg-[var(--color-amber)]/12",
}

export default function AgentsPage() {
  const { address, username } = useWallet()
  const { data: agents = [], isLoading: agentsLoading } = useAgents()
  const { data: trades = [], isLoading: tradesLoading } = useTrades()

  const totals = useMemo(() => {
    const realisedByAgent: Record<string, number> = {}
    let realised = 0
    let tradeCount = 0
    let winCount = 0
    for (const t of trades) {
      if (t.pnl == null) continue
      realised += t.pnl
      realisedByAgent[t.agent_id] = (realisedByAgent[t.agent_id] ?? 0) + t.pnl
      tradeCount += 1
      if (t.pnl > 0) winCount += 1
    }
    const unrealised = agents.reduce((sum, a) => sum + (a.unrealised_pnl ?? 0), 0)
    return {
      realised,
      unrealised,
      total: realised + unrealised,
      tradeCount,
      winRate: tradeCount ? winCount / tradeCount : 0,
      realisedByAgent,
    }
  }, [agents, trades])

  const aliveCount = agents.filter((a) => a.status === "alive").length
  const haltedCount = agents.filter((a) => a.status === "halted").length
  const loading = agentsLoading || tradesLoading

  return (
    <div className="space-y-10">
      <PageHeader
        title="Your agents"
        subtitle={
          <>
            Signed in as{" "}
            <span className="text-foreground/85">
              {displayName(address, username)}
            </span>
          </>
        }
        action={
          <Link
            href="/app/agents/new"
            className="focus-ring inline-flex items-center gap-2 rounded-md bg-[var(--color-accent-warm)] px-4 py-2 text-sm font-semibold text-[var(--color-surface)] shadow-[0_8px_24px_-12px_rgba(232,162,122,0.7)] transition hover:bg-[var(--color-accent-warm-hover)]"
          >
            <Plus size={16} />
            New agent
          </Link>
        }
      />

      <PendingHub what="Agent list + trades come from GET /api/v1/u/agents and /u/agents/{id}/trades." />

      <div className="flex items-center justify-between gap-3 text-xs text-foreground/55">
        <span className="truncate">
          {agents.length} agents · {totals.tradeCount} closed trades in fixture set.
        </span>
        <KillSwitch
          aliveCount={aliveCount}
          haltedCount={haltedCount}
          totalCount={agents.length}
        />
      </div>

      {/* ── Stat strip — flat elevated cards, no borders ───────────────── */}
      {loading ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={112} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          <StatCard
            label="Total PnL"
            value={fmtInit(totals.total)}
            tone={toneOf(totals.total)}
            hint={`${fmtInit(totals.realised)} realised · ${fmtInit(totals.unrealised)} open`}
          />
          <StatCard
            label="Realised"
            value={fmtInit(totals.realised)}
            tone={toneOf(totals.realised)}
            hint="Closed trade PnL"
          />
          <StatCard
            label="Unrealised"
            value={fmtInit(totals.unrealised)}
            tone={toneOf(totals.unrealised)}
            hint="Open positions"
          />
          <StatCard
            label="Win rate"
            value={`${(totals.winRate * 100).toFixed(0)}%`}
            tone="neutral"
            hint={`${totals.tradeCount} closed`}
            icon={<Target size={13} />}
          />
        </div>
      )}

      {/* ── PnL chart — sunken well ────────────────────────────────────── */}
      <section className="surface-sunken p-5 md:p-7">
        <header className="mb-5 flex items-baseline justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold tracking-tight text-foreground">
              Cumulative PnL
            </h3>
            <p className="mt-1 text-xs text-foreground/55">
              Realised PnL from closed trades, per agent. Zero line dashed.
            </p>
          </div>
          <span
            className={`num-tabular font-mono text-base ${toneClass(totals.realised)}`}
          >
            {fmtInit(totals.realised)}
          </span>
        </header>
        {loading ? (
          <Skeleton height={320} />
        ) : (
          <PnlChart agents={agents} trades={trades} height={320} />
        )}
      </section>

      {/* ── Agent grid ─────────────────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={240} />
          ))}
        </div>
      ) : agents.length === 0 ? (
        <EmptyState
          icon={<Inbox size={20} />}
          title="No agents yet"
          body="Spawn your first agent to start letting the hub trade on your behalf. Strategies and credits must be set up first."
          cta={
            <Link
              href="/app/agents/new"
              className="focus-ring inline-flex items-center gap-2 rounded-md bg-[var(--color-accent-warm)] px-4 py-2 text-sm font-semibold text-[var(--color-surface)] hover:bg-[var(--color-accent-warm-hover)]"
            >
              <Plus size={16} />
              Create agent
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {agents.map((a: Agent) => (
            <AgentCard
              key={a.id}
              agent={a}
              realised={totals.realisedByAgent[a.id] ?? 0}
              trades={trades.filter((t) => t.agent_id === a.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Agent card ──────────────────────────────────────────────────────────────

function AgentCard({
  agent,
  realised,
  trades,
}: {
  agent: Agent
  realised: number
  trades: readonly DemoTrade[]
}) {
  const unrealised = agent.unrealised_pnl ?? 0
  const currentValue = agent.amount_usdt + unrealised
  const valueTone = toneClass(unrealised)

  return (
    <Link
      href={`/app/agents/${agent.id}`}
      className="hover-lift surface group relative flex flex-col overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-warm)]/60"
    >
      {/* Header — name + status */}
      <div className="flex items-start justify-between gap-3 px-6 pt-5">
        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold tracking-tight text-foreground">
            {agent.name}
          </p>
          <p className="mt-1 font-mono text-[11px] text-foreground/50">
            {agent.symbol}
          </p>
        </div>
        <StatusBadge status={agent.status} />
      </div>

      {/* Value + realised */}
      <div className="flex items-end justify-between gap-3 px-6 pt-5 pb-3">
        <div>
          <div className="label-xs">Value</div>
          <div
            className={`num-tabular mt-1.5 font-mono text-[26px] font-semibold leading-none tracking-tight ${valueTone}`}
          >
            {usdToInit(currentValue).toLocaleString(undefined, { maximumFractionDigits: 2 })}
            <span className="ml-1 text-[14px] font-medium text-foreground/50">INIT</span>
          </div>
        </div>
        <div className="text-right">
          <div className="label-xs">Realised</div>
          <div className={`num-tabular mt-1.5 font-mono text-sm ${toneClass(realised)}`}>
            {fmtInit(realised)}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-[160px]">
        <PnlChartCard agent={agent} trades={trades} height={160} minimal />
      </div>

      <div className="flex items-center justify-between bg-[var(--color-surface-sunken)]/50 px-6 py-3 text-[11px] text-foreground/55">
        <span className="inline-flex items-center gap-1.5">
          <SideDot side={agent.side} />
          <span className="capitalize">{agent.side}</span>
          <span className="text-foreground/30">·</span>
          <span className="num-tabular font-mono">{agent.price.toLocaleString()}</span>
        </span>
        <span className="text-[var(--color-accent-warm)] opacity-0 transition group-hover:opacity-100">
          View →
        </span>
      </div>
    </Link>
  )
}

function StatusBadge({ status }: { status: AgentStatusT }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${STATUS_TONE[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  )
}

function SideDot({ side }: { side: Agent["side"] }) {
  const color =
    side === "long"
      ? "var(--color-teal)"
      : side === "short"
        ? "var(--color-red-light)"
        : "rgba(242,240,235,0.3)"
  return (
    <span
      className="inline-block h-1.5 w-1.5 rounded-full"
      style={{ background: color }}
    />
  )
}

// ── Stat card — no border, elevation tiers ──────────────────────────────────

type Tone = "positive" | "negative" | "neutral"

function StatCard({
  label,
  value,
  tone,
  hint,
  emphasis,
  icon,
}: {
  label: string
  value: string
  tone: Tone
  hint?: string
  emphasis?: boolean
  icon?: React.ReactNode
}) {
  const toneText =
    tone === "positive"
      ? "text-[var(--color-teal)]"
      : tone === "negative"
        ? "text-[var(--color-red-light)]"
        : "text-foreground"

  const ArrowIcon =
    tone === "positive"
      ? ArrowUpRight
      : tone === "negative"
        ? ArrowDownRight
        : TrendingUp

  return (
    <div
      className={`relative flex flex-col justify-between rounded-2xl p-5 transition ${
        emphasis
          ? "surface-accent bg-[var(--color-accent-warm-soft)]"
          : "surface"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="label-xs">{label}</span>
        <span
          className={`flex h-7 w-7 items-center justify-center rounded-full ${
            emphasis
              ? "bg-[var(--color-accent-warm)]/20 text-[var(--color-accent-warm)]"
              : `bg-white/[0.04] ${toneText}`
          }`}
        >
          {icon ?? <ArrowIcon size={13} />}
        </span>
      </div>
      <p
        className={`num-tabular mt-4 font-mono text-[28px] font-semibold leading-none tracking-tight ${toneText}`}
      >
        {value}
      </p>
      <p className="mt-2.5 truncate text-[11px] text-foreground/50">
        {hint ?? "USDT"}
      </p>
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function toneOf(v: number): Tone {
  if (v > 0) return "positive"
  if (v < 0) return "negative"
  return "neutral"
}

function toneClass(v: number) {
  if (v > 0) return "text-[var(--color-teal)]"
  if (v < 0) return "text-[var(--color-red-light)]"
  return "text-foreground/75"
}

