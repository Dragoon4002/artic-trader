"use client"

import Link from "next/link"
import { use, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Play, Square, Trash2 } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { PnlChartCard } from "@/components/dashboard/pnl-chart"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useAgent, useDeleteAgent, useLogs, useStartAgent, useStopAgent, useTrades } from "@/hooks/use-queries"
import { useHubAuth } from "@/hooks/use-hub-auth"
import type { AgentStatusT, LogLevelT } from "@/lib/schemas"
import { explorerTxUrl, shortHash } from "@/lib/chain"

const STATUS_TONE: Record<AgentStatusT, string> = {
  alive: "text-[var(--color-teal)] bg-[var(--color-teal)]/12",
  starting: "text-[var(--color-accent-warm)] bg-[var(--color-accent-warm-soft)]",
  stopped: "text-foreground/55 bg-white/[0.05]",
  error: "text-[var(--color-red-light)] bg-[var(--color-red)]/12",
  halted: "text-[var(--color-amber)] bg-[var(--color-amber)]/12",
}

const LOG_LEVELS: { key: LogLevelT; color: string }[] = [
  { key: "init", color: "text-foreground/45" },
  { key: "llm", color: "text-[var(--color-blue-light)]" },
  { key: "tick", color: "text-foreground/55" },
  { key: "action", color: "text-[var(--color-accent-warm)]" },
  { key: "sl_tp", color: "text-[var(--color-amber)]" },
  { key: "supervisor", color: "text-[var(--color-blue-light)]" },
  { key: "warn", color: "text-[var(--color-amber)]" },
  { key: "error", color: "text-[var(--color-red-light)]" },
  { key: "info", color: "text-foreground/55" },
  { key: "debug", color: "text-foreground/40" },
]

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { token, status: authStatus, run: hubSignIn, hydrated: authHydrated } = useHubAuth()
  const { data: agent, isLoading: agentLoading } = useAgent(id)
  const { data: allTrades = [], isLoading: tradesLoading } = useTrades(agent?.id)
  const { data: logs = [], isLoading: logsLoading } = useLogs(agent?.id ?? "")
  const startMut = useStartAgent()
  const stopMut = useStopAgent()
  const deleteMut = useDeleteAgent()

  useEffect(() => {
    if (authHydrated && !token && authStatus === "idle") hubSignIn()
  }, [authHydrated, token, authStatus, hubSignIn])

  const busy = startMut.isPending || stopMut.isPending || deleteMut.isPending

  // Log-level filter — all on by default; toggle per level.
  const [enabled, setEnabled] = useState<Record<LogLevelT, boolean>>({
    init: true,
    llm: true,
    tick: true,
    action: true,
    sl_tp: true,
    supervisor: true,
    warn: true,
    error: true,
    info: true,
    debug: true,
  })
  const [streamLogs, setStreamLogs] = useState<typeof logs>([])

  useEffect(() => {
    if (!token || !agent?.id) return
    const HUB_URL =
      (process.env.NEXT_PUBLIC_HUB_URL as string | undefined) ?? "http://localhost:9000"
    const wsBase = HUB_URL.replace(/^http/, "ws")
    const url = `${wsBase}/ws/u/agents/${agent.id}/logs?token=${encodeURIComponent(token.access_token)}`
    let cancelled = false
    let socket: WebSocket | null = null
    try {
      socket = new WebSocket(url)
    } catch {
      return
    }
    socket.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        if (data.type !== "log") return
        if (!data.level || !data.message) return
        const entry = {
          level: data.level as LogLevelT,
          message: data.message as string,
          timestamp: data.timestamp as string,
        }
        if (!cancelled) setStreamLogs((prev) => [...prev.slice(-499), entry])
      } catch {
        /* ignore malformed frames */
      }
    }
    socket.onerror = () => {
      /* fall back to react-query polling already running */
    }
    return () => {
      cancelled = true
      try {
        socket?.close()
      } catch {
        /* ignore */
      }
    }
  }, [token, agent?.id])

  const mergedLogs = useMemo(() => {
    if (streamLogs.length === 0) return logs
    const seen = new Set(logs.map((l) => `${l.timestamp}|${l.message}`))
    const extra = streamLogs.filter((l) => !seen.has(`${l.timestamp}|${l.message}`))
    return [...logs, ...extra]
  }, [logs, streamLogs])

  const visibleLogs = useMemo(
    () => mergedLogs.filter((l) => enabled[l.level]),
    [mergedLogs, enabled]
  )

  const trades = allTrades
  const closedPnls = useMemo(
    () => trades.filter((t) => t.pnl != null).map((t) => t.pnl as number),
    [trades]
  )
  const totalPnl = closedPnls.reduce((a, b) => a + b, 0)
  const wins = closedPnls.filter((p) => p > 0).length
  const winRate = closedPnls.length ? wins / closedPnls.length : 0

  if (agentLoading) {
    return (
      <div className="space-y-6">
        <Skeleton height={36} className="w-48" />
        <Skeleton height={320} />
        <Skeleton height={260} />
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="surface p-10 text-center text-sm text-foreground/65">
        Agent not found.{" "}
        <Link
          href="/app/agents"
          className="text-[var(--color-accent-warm)] underline underline-offset-4 hover:text-[var(--color-accent-warm-hover)]"
        >
          Back to agents
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <Link
        href="/app/agents"
        className="focus-ring inline-flex items-center gap-1.5 rounded text-xs text-foreground/55 transition hover:text-foreground"
      >
        <ArrowLeft size={12} /> Back to agents
      </Link>

      <PageHeader
        title={agent.name}
        subtitle={
          <span className="inline-flex items-center gap-2">
            <span className="font-mono">{agent.symbol}</span>
            <span className="text-foreground/30">·</span>
            <span
              className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${STATUS_TONE[agent.status]}`}
            >
              {agent.status}
            </span>
            <span className="text-foreground/30">·</span>
          </span>
        }
        action={
          <div className="flex items-center gap-2">
            <IconBtn
              disabled={!token || busy || agent.status === "alive"}
              icon={<Play size={14} />}
              label={startMut.isPending ? "Starting…" : "Start"}
              onClick={() => startMut.mutate(id)}
            />
            <IconBtn
              disabled={!token || busy || agent.status !== "alive"}
              icon={<Square size={14} />}
              label={stopMut.isPending ? "Stopping…" : "Stop"}
              onClick={() => stopMut.mutate(id)}
            />
            <IconBtn
              disabled={!token || busy || agent.status === "alive"}
              danger
              icon={<Trash2 size={14} />}
              label={deleteMut.isPending ? "Deleting…" : "Delete"}
              onClick={() => deleteMut.mutate(id, { onSuccess: () => router.push("/app/agents") })}
            />
          </div>
        }
      />

      <PendingHub what="Live status + trade history + log stream come from hub WebSocket + REST." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card title="Live status">
          <Kv label="Symbol" value={agent.symbol} />
          <Kv label="Price" value={agent.price.toLocaleString()} />
          <Kv
            label="Position"
            value={
              agent.side === "flat" ? (
                <span className="text-foreground/40">flat</span>
              ) : agent.side === "long" ? (
                <span className="text-[var(--color-teal)]">long</span>
              ) : (
                <span className="text-[var(--color-red-light)]">short</span>
              )
            }
          />
          <Kv
            label="Unrealised PnL"
            value={
              agent.unrealised_pnl == null ? (
                <span className="text-foreground/40">—</span>
              ) : agent.unrealised_pnl >= 0 ? (
                <span className="text-[var(--color-teal)]">+{agent.unrealised_pnl.toFixed(2)} USDT</span>
              ) : (
                <span className="text-[var(--color-red-light)]">{agent.unrealised_pnl.toFixed(2)} USDT</span>
              )
            }
          />
          <Kv label="Strategy" value={<span className="font-mono">{agent.strategy}</span>} />
          <Kv label="LLM" value={`${agent.llm_provider} · ${agent.llm_model}`} />
        </Card>

        <Card title="Config">
          <Kv label="Amount" value={`${agent.amount_usdt} USDT`} />
          <Kv label="Leverage" value={`${agent.leverage}×`} />
          <Kv
            label="TP / SL"
            value={`${agent.tp_pct ?? "—"}% / ${agent.sl_pct ?? "—"}%`}
          />
          <Kv label="Poll" value={`${agent.poll_seconds}s`} />
          <Kv label="Supervisor" value={`${agent.supervisor_interval}s`} />
          <Kv label="Mode" value="paper" />
        </Card>

        <Card title="Performance (session)">
          <Kv label="Trades" value={trades.length.toString()} />
          <Kv label="Closed" value={closedPnls.length.toString()} />
          <Kv
            label="Win rate"
            value={closedPnls.length ? `${(winRate * 100).toFixed(0)}%` : "—"}
          />
          <Kv
            label="Total PnL"
            value={
              closedPnls.length === 0 ? (
                <span className="text-foreground/40">—</span>
              ) : totalPnl >= 0 ? (
                <span className="text-[var(--color-teal)]">+{usdToInit(totalPnl).toFixed(2)} INIT</span>
              ) : (
                <span className="text-[var(--color-red-light)]">{usdToInit(totalPnl).toFixed(2)} INIT</span>
              )
            }
          />
        </Card>
      </div>

      {/* Per-agent cumulative PnL chart */}
      <Card title="Cumulative PnL">
        {tradesLoading ? (
          <Skeleton height={240} />
        ) : (
          <PnlChartCard agent={agent} trades={trades} height={240} />
        )}
      </Card>

      <Card title="Trade history">
        {tradesLoading ? (
          <Skeleton height={180} />
        ) : trades.length === 0 ? (
          <p className="py-8 text-center text-sm text-foreground/40">No trades yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[rgba(194,203,212,0.06)] text-left text-[11px] uppercase tracking-wider text-foreground/55">
                <th className="py-2 pr-3">Side</th>
                <th className="py-2 pr-3">Entry</th>
                <th className="py-2 pr-3">Exit</th>
                <th className="py-2 pr-3">Size</th>
                <th className="py-2 pr-3">PnL</th>
                <th className="py-2 pr-3">Close</th>
                <th className="py-2 pr-3">Opened</th>
                <th className="py-2">On-chain</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} className="border-b border-[rgba(194,203,212,0.04)] transition last:border-b-0 hover:bg-white/[0.02]">
                  <td className="py-2.5 pr-3">
                    <span
                      className={
                        t.side === "long"
                          ? "text-[var(--color-teal)]"
                          : "text-[var(--color-red-light)]"
                      }
                    >
                      {t.side}
                    </span>
                  </td>
                  <td className="py-2.5 pr-3 font-mono text-foreground/70">{t.entry_price}</td>
                  <td className="py-2.5 pr-3 font-mono text-foreground/70">
                    {t.exit_price ?? <span className="text-foreground/30">open</span>}
                  </td>
                  <td className="py-2.5 pr-3 font-mono text-foreground/70">{usdToInit(t.size_usdt).toFixed(2)}</td>
                  <td className="py-2.5 pr-3 font-mono">
                    {t.pnl == null ? (
                      <span className="text-foreground/30">—</span>
                    ) : t.pnl >= 0 ? (
                      <span className="text-[var(--color-teal)]">+{usdToInit(t.pnl).toFixed(2)}</span>
                    ) : (
                      <span className="text-[var(--color-red-light)]">{usdToInit(t.pnl).toFixed(2)}</span>
                    )}
                  </td>
                  <td className="py-2.5 pr-3 text-[11px] uppercase tracking-wider text-foreground/50">
                    {t.close_reason ?? "—"}
                  </td>
                  <td className="py-2.5 pr-3 font-mono text-[11px] text-foreground/40">
                    {t.opened_at.slice(11, 19)}
                  </td>
                  <td className="py-2.5 font-mono text-[11px]">
                    {t.tx_hash ? (
                      <a
                        href={explorerTxUrl(t.tx_hash) ?? "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[var(--color-blue-light)] hover:underline"
                        title={t.tx_hash}
                      >
                        {shortHash(t.tx_hash)} ↗
                      </a>
                    ) : (
                      <span className="text-foreground/30">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card
        title="Log stream"
        right={
          <LogFilter
            enabled={enabled}
            onToggle={(k) => setEnabled((e) => ({ ...e, [k]: !e[k] }))}
            counts={countByLevel(logs)}
          />
        }
      >
        {logsLoading ? (
          <Skeleton height={200} />
        ) : (
          <pre className="max-h-64 overflow-auto p-4 font-mono text-xs leading-relaxed">
            {visibleLogs.length === 0 ? (
              <span className="text-foreground/30">No log lines match current filter.</span>
            ) : (
              visibleLogs.map((l, i) => {
                const tone = LOG_LEVELS.find((x) => x.key === l.level)?.color ?? "text-foreground/50"
                return (
                  <div key={i} className={tone}>
                    <span className="text-foreground/30">{l.timestamp}</span>{" "}
                    <span className="text-foreground/40">[{l.level}]</span> {l.message}
                  </div>
                )
              })
            )}
          </pre>
        )}
      </Card>
    </div>
  )
}

function countByLevel(logs: { level: LogLevelT }[]): Record<LogLevelT, number> {
  const out: Record<LogLevelT, number> = {
    init: 0, llm: 0, tick: 0, action: 0, sl_tp: 0, supervisor: 0, warn: 0, error: 0, info: 0, debug: 0,
  }
  for (const l of logs) out[l.level] = (out[l.level] ?? 0) + 1
  return out
}

function LogFilter({
  enabled,
  onToggle,
  counts,
}: {
  enabled: Record<LogLevelT, boolean>
  onToggle: (k: LogLevelT) => void
  counts: Record<LogLevelT, number>
}) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {LOG_LEVELS.map(({ key, color }) => {
        const on = enabled[key]
        const c = counts[key] ?? 0
        return (
          <button
            key={key}
            onClick={() => onToggle(key)}
            className={`focus-ring inline-flex items-center gap-1 rounded-md px-2 py-1 font-mono text-[10px] uppercase tracking-wider transition ${
              on
                ? `${color} bg-white/[0.05]`
                : "bg-transparent text-foreground/35 hover:bg-white/[0.02] hover:text-foreground/60"
            }`}
            title={`${on ? "Hide" : "Show"} ${key} (${c})`}
          >
            {key}
            <span className="text-foreground/30">{c}</span>
          </button>
        )
      })}
    </div>
  )
}

function Card({
  title,
  right,
  children,
}: {
  title: string
  right?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="surface p-6">
      <header className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-foreground/55">
          {title}
        </h3>
        {right}
      </header>
      {children}
    </section>
  )
}

function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[rgba(194,203,212,0.04)] py-2.5 text-sm last:border-b-0">
      <span className="text-foreground/55">{label}</span>
      <span className="num-tabular truncate text-right font-mono text-foreground/90">
        {value}
      </span>
    </div>
  )
}

function IconBtn({
  icon,
  label,
  disabled,
  danger,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  disabled?: boolean
  danger?: boolean
  onClick?: () => void
}) {
  const base =
    "focus-ring inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition"
  const tone = danger
    ? "bg-[var(--color-red)]/10 text-[var(--color-red-light)] hover:bg-[var(--color-red)]/18"
    : "bg-white/[0.04] text-foreground/80 hover:bg-white/[0.07] hover:text-foreground"
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`${base} ${tone} ${disabled ? "btn-disabled" : ""}`}
    >
      {icon}
      {label}
    </button>
  )
}
