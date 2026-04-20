"use client"

import { useMemo } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { DemoAgent, DemoTrade } from "@/lib/demo-data"

const SERIES_COLORS = [
  "var(--color-orange)",
  "var(--color-blue-accent)",
  "var(--color-teal)",
  "#E4B54B", // amber — distinct from red-light, signals "neutral/warn"
]

interface Point {
  t: number // epoch ms (X axis)
  label: string // ISO-ish human tick
  [agentKey: string]: number | string
}

export interface PnlChartProps {
  agents: readonly DemoAgent[]
  trades: readonly DemoTrade[]
  height?: number
}

/**
 * Per-agent cumulative realised PnL over time. Each series = one agent;
 * filled with a gradient that fades to transparent at the bottom. Y axis
 * crosses zero so losses render below the midline.
 */
export function PnlChart({ agents, trades, height = 300 }: PnlChartProps) {
  const { data, agentKeys } = useMemo(() => build(agents, trades), [agents, trades])

  if (data.length <= 1) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-dashed border-white/10 bg-white/[0.01] text-sm text-foreground/40"
        style={{ height }}
      >
        Not enough closed trades yet to plot.
      </div>
    )
  }

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            {agentKeys.map((a, i) => {
              const color = SERIES_COLORS[i % SERIES_COLORS.length]
              return (
                <linearGradient id={`g-${a.id}`} key={a.id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              )
            })}
          </defs>

          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />

          <XAxis
            dataKey="label"
            stroke="rgba(240,237,237,0.35)"
            tick={{ fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            minTickGap={32}
          />
          <YAxis
            stroke="rgba(240,237,237,0.35)"
            tick={{ fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={44}
            tickFormatter={(v: number) =>
              v > 0 ? `+${v.toFixed(0)}` : v.toFixed(0)
            }
          />

          <ReferenceLine
            y={0}
            stroke="rgba(240,237,237,0.25)"
            strokeDasharray="3 3"
          />

          <Tooltip content={<PnlTooltip agents={agentKeys} />} />

          {agentKeys.map((a, i) => {
            const color = SERIES_COLORS[i % SERIES_COLORS.length]
            return (
              <Area
                key={a.id}
                type="monotone"
                dataKey={a.id}
                name={a.name}
                stroke={color}
                strokeWidth={2}
                fill={`url(#g-${a.id})`}
                isAnimationActive={false}
                connectNulls
              />
            )
          })}
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-3 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs">
        {agentKeys.map((a, i) => (
          <div key={a.id} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }}
            />
            <span className="text-foreground/70">{a.name}</span>
            <span className="font-mono text-foreground/40">({a.symbol})</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function build(agents: readonly DemoAgent[], trades: readonly DemoTrade[]) {
  const agentKeys = agents.map((a) => ({ id: a.id, name: a.name, symbol: a.symbol }))

  const closed = trades
    .filter((t) => t.pnl != null && t.closed_at)
    .sort((a, b) => a.closed_at!.localeCompare(b.closed_at!))

  if (closed.length === 0) {
    return { data: [], agentKeys }
  }

  const running: Record<string, number> = Object.fromEntries(agentKeys.map((a) => [a.id, 0]))
  const startTs = new Date(closed[0].closed_at!).getTime() - 1

  const data: Point[] = [
    {
      t: startTs,
      label: fmtTick(new Date(startTs)),
      ...Object.fromEntries(agentKeys.map((a) => [a.id, 0])),
    },
  ]

  for (const tr of closed) {
    running[tr.agent_id] = (running[tr.agent_id] ?? 0) + (tr.pnl as number)
    const ts = new Date(tr.closed_at!).getTime()
    data.push({
      t: ts,
      label: fmtTick(new Date(tr.closed_at!)),
      ...Object.fromEntries(agentKeys.map((a) => [a.id, running[a.id] ?? 0])),
    })
  }

  return { data, agentKeys }
}

function fmtTick(d: Date) {
  // Compact "Apr 19 14:02" style
  const month = d.toLocaleString("en-US", { month: "short", timeZone: "UTC" })
  const day = d.getUTCDate().toString().padStart(2, "0")
  const h = d.getUTCHours().toString().padStart(2, "0")
  const m = d.getUTCMinutes().toString().padStart(2, "0")
  return `${month} ${day} ${h}:${m}`
}

interface TooltipPayloadRow {
  dataKey?: string | number
  value?: number | string
  color?: string
}
interface PnlTooltipProps {
  active?: boolean
  payload?: TooltipPayloadRow[]
  label?: string | number
  agents: { id: string; name: string }[]
}

function PnlTooltip({ active, payload, label, agents }: PnlTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  // Sort descending so winners show first
  const rows = payload
    .map((p: TooltipPayloadRow) => ({
      id: String(p.dataKey),
      name: agents.find((a) => a.id === p.dataKey)?.name ?? "?",
      value: Number(p.value ?? 0),
      color: p.color ?? "#fff",
    }))
    .sort((a: { value: number }, b: { value: number }) => b.value - a.value)

  const total = rows.reduce(
    (s: number, r: { value: number }) => s + r.value,
    0
  )

  return (
    <div className="rounded-md border border-white/10 bg-[var(--color-surface)]/95 p-3 shadow-xl backdrop-blur">
      <p className="mb-2 text-[11px] font-mono text-foreground/50">{label}</p>
      <ul className="space-y-1 text-xs">
        {rows.map((r) => (
          <li key={r.id} className="flex items-center gap-3">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: r.color }}
            />
            <span className="flex-1 text-foreground/80">{r.name}</span>
            <span
              className={`font-mono ${
                r.value > 0
                  ? "text-[var(--color-teal)]"
                  : r.value < 0
                    ? "text-[var(--color-red-light)]"
                    : "text-foreground/60"
              }`}
            >
              {fmt(r.value)}
            </span>
          </li>
        ))}
        <li className="mt-1.5 flex items-center gap-3 border-t border-white/10 pt-1.5">
          <span className="flex-1 text-[11px] uppercase tracking-wide text-foreground/50">
            Total
          </span>
          <span
            className={`font-mono ${
              total > 0
                ? "text-[var(--color-teal)]"
                : total < 0
                  ? "text-[var(--color-red-light)]"
                  : "text-foreground/60"
            }`}
          >
            {fmt(total)}
          </span>
        </li>
      </ul>
    </div>
  )
}

function fmt(v: number) {
  const abs = Math.abs(v)
  const sign = v > 0 ? "+" : v < 0 ? "-" : ""
  return `${sign}${abs.toFixed(2)}`
}
