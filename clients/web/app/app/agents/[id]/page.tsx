"use client"

import Link from "next/link"
import { use } from "react"
import { ArrowLeft, Play, Square, Trash2 } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { demoAgents, demoLogs, demoTrades, findDemoAgent, AgentStatus } from "@/lib/demo-data"

const STATUS_TONE: Record<AgentStatus, string> = {
  alive: "text-[var(--color-teal)] bg-[var(--color-teal)]/10 border-[var(--color-teal)]/30",
  starting: "text-[var(--color-orange)] bg-[var(--color-orange)]/10 border-[var(--color-orange)]/30",
  stopped: "text-foreground/50 bg-white/[0.04] border-white/10",
  error: "text-[var(--color-red-light)] bg-[var(--color-red)]/10 border-[var(--color-red)]/30",
  halted: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
}

const LOG_TONE: Record<string, string> = {
  init: "text-foreground/40",
  llm: "text-[var(--color-blue-accent)]",
  tick: "text-foreground/50",
  action: "text-[var(--color-orange)]",
  sl_tp: "text-yellow-400",
  supervisor: "text-[var(--color-blue-accent)]",
  warn: "text-yellow-400",
  error: "text-[var(--color-red-light)]",
}

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const agent = findDemoAgent(id) ?? demoAgents[0]
  const trades = demoTrades.filter((t) => t.agent_id === agent.id)
  const closedPnls = trades.filter((t) => t.pnl != null).map((t) => t.pnl as number)
  const totalPnl = closedPnls.reduce((a, b) => a + b, 0)
  const wins = closedPnls.filter((p) => p > 0).length
  const winRate = closedPnls.length ? wins / closedPnls.length : 0
  return (
    <div className="space-y-8">
      <Link
        href="/app/agents"
        className="inline-flex items-center gap-1.5 text-xs text-foreground/50 hover:text-foreground"
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
            <DemoBadge />
          </span>
        }
        action={
          <div className="flex items-center gap-2">
            <IconBtn disabled icon={<Play size={14} />} label="Start" />
            <IconBtn disabled icon={<Square size={14} />} label="Stop" />
            <IconBtn disabled danger icon={<Trash2 size={14} />} label="Delete" />
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
                <span className="text-[var(--color-teal)]">+{totalPnl.toFixed(2)} USDT</span>
              ) : (
                <span className="text-[var(--color-red-light)]">{totalPnl.toFixed(2)} USDT</span>
              )
            }
          />
        </Card>
      </div>

      <Card title="Trade history">
        {trades.length === 0 ? (
          <p className="py-8 text-center text-sm text-foreground/40">No trades yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-[11px] uppercase tracking-wide text-foreground/50">
                <th className="py-2 pr-3">Side</th>
                <th className="py-2 pr-3">Entry</th>
                <th className="py-2 pr-3">Exit</th>
                <th className="py-2 pr-3">Size</th>
                <th className="py-2 pr-3">PnL</th>
                <th className="py-2 pr-3">Close</th>
                <th className="py-2">Opened</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} className="border-b border-white/5 last:border-b-0">
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
                  <td className="py-2.5 pr-3 font-mono text-foreground/70">{t.size_usdt}</td>
                  <td className="py-2.5 pr-3 font-mono">
                    {t.pnl == null ? (
                      <span className="text-foreground/30">—</span>
                    ) : t.pnl >= 0 ? (
                      <span className="text-[var(--color-teal)]">+{t.pnl.toFixed(2)}</span>
                    ) : (
                      <span className="text-[var(--color-red-light)]">{t.pnl.toFixed(2)}</span>
                    )}
                  </td>
                  <td className="py-2.5 pr-3 text-[11px] uppercase tracking-wider text-foreground/50">
                    {t.close_reason ?? "—"}
                  </td>
                  <td className="py-2.5 font-mono text-[11px] text-foreground/40">
                    {t.opened_at.slice(11, 19)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="Log stream">
        <pre className="max-h-64 overflow-auto rounded bg-black/40 p-4 font-mono text-xs leading-relaxed">
          {demoLogs.map((l, i) => (
            <div key={i} className={LOG_TONE[l.level] ?? "text-foreground/50"}>
              <span className="text-foreground/30">{l.timestamp}</span>{" "}
              <span className="text-foreground/40">[{l.level}]</span> {l.message}
            </div>
          ))}
        </pre>
      </Card>
    </div>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-wide text-foreground/50">{title}</h3>
      {children}
    </section>
  )
}

function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 py-1.5 text-sm last:border-b-0">
      <span className="text-foreground/50">{label}</span>
      <span className="font-mono text-foreground/80">{value}</span>
    </div>
  )
}

function IconBtn({
  icon,
  label,
  disabled,
  danger,
}: {
  icon: React.ReactNode
  label: string
  disabled?: boolean
  danger?: boolean
}) {
  const base =
    "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-semibold transition"
  const tone = danger
    ? "border-[var(--color-red)]/30 text-[var(--color-red-light)] hover:bg-[var(--color-red)]/10"
    : "border-white/10 bg-white/[0.03] text-foreground/70 hover:text-foreground"
  return (
    <button
      disabled={disabled}
      title={disabled ? "Hub auth wiring pending" : undefined}
      className={`${base} ${tone} ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
    >
      {icon}
      {label}
    </button>
  )
}
