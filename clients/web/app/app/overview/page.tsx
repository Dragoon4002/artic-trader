"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { ArrowRight, ArrowUpRight, ArrowDownRight, Activity, Wallet, Copy, Check, Target, TrendingUp, Trophy, BookOpen } from "lucide-react"
import { useAgents, useStrategies, useChainWallet, useTrades } from "@/hooks/use-queries"
import { PageHeader } from "@/components/dashboard/empty-state"
import { Skeleton } from "@/components/dashboard/skeleton"
import { PnlAreaChart } from "@/components/dashboard/overview/pnl-area-chart"
import type { AgentStatusT } from "@/lib/schemas"

const DAY = 24 * 60 * 60 * 1000

const STATUS_TONE: Record<AgentStatusT, string> = {
  alive:    "text-[var(--color-teal)] bg-[var(--color-teal)]/12",
  starting: "text-[var(--color-accent-warm)] bg-[var(--color-accent-warm-soft)]",
  stopped:  "text-foreground/55 bg-white/[0.05]",
  error:    "text-[var(--color-red-light)] bg-[var(--color-red)]/12",
  halted:   "text-[var(--color-amber)] bg-[var(--color-amber)]/12",
}

const ALLOC_COLORS = [
  "var(--color-teal)",
  "var(--color-accent-warm)",
  "var(--color-blue-accent)",
  "var(--color-amber)",
  "var(--color-red-light)",
]

const RANK_TONE = [
  "bg-[var(--color-accent-warm)] text-[var(--color-surface)]",                           // 1
  "bg-[var(--color-blue-accent)] text-[var(--color-surface)]",                           // 2
  "bg-[var(--color-amber)] text-[var(--color-surface)]",                                 // 3
  "bg-white/[0.06] text-foreground/70",                                                  // 4
  "bg-white/[0.06] text-foreground/70",                                                  // 5
]

function fmtMoney(v: number) {
  const sign = v > 0 ? "+" : v < 0 ? "-" : ""
  return `${sign}$${Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
function pnlTone(v: number) {
  if (v > 0) return "text-[var(--color-teal)]"
  if (v < 0) return "text-[var(--color-red-light)]"
  return "text-foreground/55"
}
function timeAgo(iso: string | null | undefined) {
  if (!iso) return "—"
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60_000)
  if (m < 1) return "just now"
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  return `${d}d ago`
}

export default function OverviewPage() {
  const { data: agents = [],     isLoading: agentsLoading }     = useAgents()
  const { data: trades = [],     isLoading: tradesLoading }     = useTrades()
  const { data: strategies,      isLoading: strategiesLoading } = useStrategies()
  const { data: wallet,          isLoading: walletLoading }     = useChainWallet()

  const installed = strategies?.installed ?? []
  const [now] = useState(() => Date.now())

  // ── Stat strip — totals + 30d-vs-prior-30d deltas ─────────────
  const stats = useMemo(() => {
    const cutoff30 = now - 30 * DAY
    const cutoff60 = now - 60 * DAY
    let realised = 0, tradeCount = 0, winCount = 0
    let last30 = 0, last30W = 0, last30N = 0
    let prev30 = 0, prev30W = 0, prev30N = 0
    for (const t of trades) {
      if (t.pnl == null) continue
      realised += t.pnl
      tradeCount++
      if (t.pnl > 0) winCount++
      const ts = t.closed_at ? new Date(t.closed_at).getTime() : 0
      if (ts >= cutoff30) {
        last30 += t.pnl; last30N++
        if (t.pnl > 0) last30W++
      } else if (ts >= cutoff60) {
        prev30 += t.pnl; prev30N++
        if (t.pnl > 0) prev30W++
      }
    }
    const unrealised = agents.reduce((s, a) => s + (a.unrealised_pnl ?? 0), 0)
    const total = realised + unrealised
    const winRate = tradeCount ? winCount / tradeCount : 0
    const winRateDelta = (last30N && prev30N) ? (last30W / last30N) - (prev30W / prev30N) : 0
    return { total, realised, unrealised, tradeCount, winRate, last30, prev30, pnlDelta: last30 - prev30, winRateDelta }
  }, [agents, trades, now])

  const aliveCount = agents.filter(a => a.status === "alive").length

  // ── Capital allocation by symbol ──────────────────────────────
  const alloc = useMemo(() => {
    const map = new Map<string, { symbol: string; total: number; count: number }>()
    for (const a of agents) {
      const cur = map.get(a.symbol) ?? { symbol: a.symbol, total: 0, count: 0 }
      cur.total += a.amount_usdt
      cur.count += 1
      map.set(a.symbol, cur)
    }
    const rows = Array.from(map.values()).sort((x, y) => y.total - x.total)
    const grand = rows.reduce((s, r) => s + r.total, 0)
    return { rows, grand }
  }, [agents])

  // ── Top strategies — by realised PnL ──────────────────────────
  const topStrategies = useMemo(() => {
    const map = new Map<string, { name: string; pnl: number; uses: number; trades: number }>()
    for (const t of trades) {
      if (!t.strategy) continue
      const cur = map.get(t.strategy) ?? { name: t.strategy, pnl: 0, uses: 0, trades: 0 }
      cur.pnl += t.pnl ?? 0
      cur.trades += 1
      map.set(t.strategy, cur)
    }
    for (const a of agents) {
      const cur = map.get(a.strategy) ?? { name: a.strategy, pnl: 0, uses: 0, trades: 0 }
      cur.uses += 1
      map.set(a.strategy, cur)
    }
    return Array.from(map.values()).sort((x, y) => y.pnl - x.pnl).slice(0, 5)
  }, [agents, trades])

  // ── Last trade timestamp per agent ────────────────────────────
  const lastTradeByAgent = useMemo(() => {
    const out: Record<string, string> = {}
    for (const t of trades) {
      const ts = t.closed_at || t.opened_at
      if (!ts) continue
      if (!out[t.agent_id] || out[t.agent_id]!.localeCompare(ts) < 0) out[t.agent_id] = ts
    }
    return out
  }, [trades])

  return (
    <div className="space-y-8">
      <PageHeader title="Overview" subtitle="Your agents, strategies, and account at a glance." />

      {/* ── Block A — stat strip ──────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard
          label="Total PnL"
          value={tradesLoading ? null : fmtMoney(stats.total)}
          valueTone={pnlTone(stats.total)}
          delta={stats.pnlDelta}
          deltaSuffix=" 30d"
          icon={<TrendingUp size={14} />}
        />
        <StatCard
          label="Win rate"
          value={tradesLoading ? null : stats.tradeCount ? `${(stats.winRate * 100).toFixed(1)}%` : "—"}
          valueTone="text-foreground"
          delta={stats.winRateDelta * 100}
          deltaSuffix="%"
          icon={<Target size={14} />}
        />
        <StatCard
          label="Running agents"
          value={agentsLoading ? null : `${aliveCount} / ${agents.length}`}
          valueTone={aliveCount > 0 ? "text-[var(--color-teal)]" : "text-foreground/55"}
          icon={<Activity size={14} />}
        />
        <WalletStatCard wallet={wallet} loading={walletLoading} />

      </div>

      {/* ── Block B — main row ─────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        {/* Left — PnL trend */}
        <div className="surface p-5 lg:col-span-2">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-sm font-semibold text-foreground">PnL Trend</h2>
              <p className="text-xs text-foreground/50">Cumulative realised PnL over time</p>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <Legend swatch="var(--color-teal)" label="Realised" />
            </div>
          </div>
          {tradesLoading ? <Skeleton className="h-[300px] w-full" /> : <PnlAreaChart trades={trades} height={300} />}
        </div>

        {/* Right — capital allocation */}
        <div className="surface p-5">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-foreground">Capital Allocation</h2>
            <p className="text-xs text-foreground/50">Deployed by token</p>
          </div>
          {agentsLoading ? (
            <div className="space-y-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
          ) : alloc.rows.length === 0 ? (
            <div className="py-8 text-center text-sm text-foreground/40">No capital deployed.</div>
          ) : (
            <div className="space-y-4">
              {alloc.rows.map((r, i) => {
                const pct = alloc.grand > 0 ? (r.total / alloc.grand) * 100 : 0
                const color = ALLOC_COLORS[i % ALLOC_COLORS.length]
                return (
                  <div key={r.symbol}>
                    <div className="mb-1.5 flex items-baseline justify-between gap-2">
                      <div className="flex items-baseline gap-2 min-w-0">
                        <span className="font-mono text-sm text-foreground truncate">{r.symbol}</span>
                        <span className="text-[11px] text-foreground/45">{r.count} agent{r.count > 1 ? "s" : ""}</span>
                      </div>
                      <div className="flex items-baseline gap-2">
                        <span className="num-tabular text-sm text-foreground/85">${r.total.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
                        <span className="num-tabular text-[11px] text-foreground/50 w-9 text-right">{pct.toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-white/[0.04] overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          {!agentsLoading && alloc.grand > 0 && (
            <div className="mt-5 flex items-center justify-between border-t border-white/[0.04] pt-3 text-[11px]">
              <span className="text-foreground/50">Total deployed</span>
              <span className="num-tabular font-semibold text-foreground">${alloc.grand.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Block C — bottom row ───────────────────────────────── */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {/* Agents */}
        <div className="surface p-5">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Agents</h2>
              <p className="text-xs text-foreground/50">Latest activity</p>
            </div>
            <Link href="/app/agents" className="flex items-center gap-1 text-xs text-foreground/50 hover:text-foreground transition-colors">
              View all <ArrowUpRight size={12} />
            </Link>
          </div>
          {agentsLoading ? (
            <div className="space-y-2">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
          ) : agents.length === 0 ? (
            <div className="py-8 text-center text-sm text-foreground/40">
              No agents yet.{" "}
              <Link href="/app/agents/new" className="text-[var(--color-accent-warm)] hover:underline">Create one →</Link>
            </div>
          ) : (
            <div className="-mx-1">
              {agents.slice(0, 6).map(a => {
                const pnl = a.unrealised_pnl ?? 0
                const initial = a.name.charAt(0).toUpperCase()
                const dotColor =
                  a.status === "alive"   ? "var(--color-teal)" :
                  a.status === "halted"  ? "var(--color-amber)" :
                  a.status === "error"   ? "var(--color-red-light)" :
                  a.status === "starting" ? "var(--color-accent-warm)" :
                  "rgba(194,203,212,0.3)"
                return (
                  <Link
                    key={a.id}
                    href={`/app/agents/${a.id}`}
                    className="flex items-center gap-3 rounded-lg px-1 py-2.5 hover:bg-white/[0.02] transition-colors"
                  >
                    <span
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold text-foreground"
                      style={{ background: `color-mix(in srgb, ${dotColor} 18%, transparent)`, color: dotColor }}
                    >
                      {initial}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">{a.name}</p>
                      <p className="text-[11px] text-foreground/45">
                        <span className="font-mono">{a.symbol}</span> · {timeAgo(lastTradeByAgent[a.id])}
                      </p>
                    </div>
                    <span className={`num-tabular text-sm ${pnlTone(pnl)}`}>{fmtMoney(pnl)}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${STATUS_TONE[a.status]}`}>
                      {a.status}
                    </span>
                  </Link>
                )
              })}
            </div>
          )}
        </div>

        {/* Top strategies */}
        <div className="surface p-5">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Top Strategies</h2>
              <p className="text-xs text-foreground/50">Ranked by realised PnL</p>
            </div>
            <Trophy size={14} className="text-[var(--color-amber)]" />
          </div>
          {strategiesLoading || tradesLoading ? (
            <div className="space-y-2">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
          ) : topStrategies.length === 0 ? (
            <div className="py-8 text-center text-sm text-foreground/40">
              No strategy data yet.{" "}
              <Link href="/app/strategies" className="text-[var(--color-accent-warm)] hover:underline flex items-center justify-center gap-1 mt-2">
                <BookOpen size={12} /> Browse strategies
              </Link>
            </div>
          ) : (
            <div className="-mx-1">
              {topStrategies.map((s, i) => (
                <div key={s.name} className="flex items-center gap-3 rounded-lg px-1 py-2.5">
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[12px] font-bold ${RANK_TONE[i]}`}>
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">{s.name}</p>
                    <p className="text-[11px] text-foreground/45">
                      {s.uses} agent{s.uses !== 1 ? "s" : ""} · {s.trades} trade{s.trades !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`num-tabular text-sm font-semibold ${pnlTone(s.pnl)}`}>{fmtMoney(s.pnl)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          {!strategiesLoading && installed.length > 0 && (
            <div className="mt-4 border-t border-white/[0.04] pt-3">
              <Link href="/app/strategies" className="flex items-center justify-between text-xs text-foreground/50 hover:text-foreground transition-colors">
                <span>{installed.length} strategies installed</span>
                <span className="flex items-center gap-1">View all <ArrowRight size={12} /></span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function StatCard({
  label,
  value,
  valueTone,
  delta,
  deltaSuffix,
  icon,
}: {
  label: string
  value: string | null
  valueTone: string
  delta?: number
  deltaSuffix?: string
  icon: React.ReactNode
}) {
  const showDelta = delta !== undefined && Math.abs(delta) > 0.01
  return (
    <div className="surface p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="label-xs">{label}</p>
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.04] text-foreground/50">{icon}</span>
      </div>
      {value == null
        ? <Skeleton className="h-7 w-24" />
        : (
          <div className="flex items-baseline gap-2">
            <p className={`text-[26px] font-semibold num-tabular tracking-tight ${valueTone}`}>{value}</p>
            {showDelta && (
              <span className={`flex items-center gap-0.5 text-[11px] num-tabular ${delta! >= 0 ? "text-[var(--color-teal)]" : "text-[var(--color-red-light)]"}`}>
                {delta! >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                {Math.abs(delta!).toFixed(deltaSuffix === "%" ? 1 : 0)}{deltaSuffix}
              </span>
            )}
          </div>
        )
      }
    </div>
  )
}

function WalletStatCard({
  wallet,
  loading,
}: {
  wallet: { address: string | null; balance_og: string; threshold_og: string } | undefined
  loading: boolean
}) {
  const [copied, setCopied] = useState(false)
  const balance = Number(wallet?.balance_og ?? 0)
  const threshold = Number(wallet?.threshold_og ?? 0.2)
  const tone =
    balance <= 0 ? "text-foreground/55"
    : balance < threshold ? "text-[var(--color-red-light)]"
    : balance < threshold * 5 ? "text-[var(--color-amber)]"
    : "text-[var(--color-teal)]"

  const copy = async () => {
    if (!wallet?.address) return
    await navigator.clipboard.writeText(wallet.address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="surface p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="label-xs">Wallet balance</p>
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.04] text-foreground/50">
          <Wallet size={14} />
        </span>
      </div>
      {loading || !wallet ? (
        <Skeleton className="h-7 w-24" />
      ) : (
        <>
          <div className="flex items-baseline gap-2">
            <p className={`text-[26px] font-semibold num-tabular tracking-tight ${tone}`}>
              {balance.toFixed(3)}
            </p>
            <span className="text-[11px] text-foreground/55">OG</span>
          </div>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="font-mono text-[10px] text-foreground/40">
              {wallet.address ? `${wallet.address.slice(0, 6)}…${wallet.address.slice(-4)}` : "—"}
            </span>
            <button
              onClick={copy}
              disabled={!wallet.address}
              className="focus-ring inline-flex h-4 w-4 items-center justify-center rounded text-foreground/40 hover:bg-white/10 hover:text-foreground disabled:opacity-40"
              title={copied ? "Copied!" : "Copy wallet address"}
              aria-label="Copy wallet address"
            >
              {copied ? <Check size={10} className="text-[var(--color-teal)]" /> : <Copy size={10} />}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-foreground/65">
      <span className="inline-block h-2 w-2 rounded-full" style={{ background: swatch }} />
      {label}
    </span>
  )
}
