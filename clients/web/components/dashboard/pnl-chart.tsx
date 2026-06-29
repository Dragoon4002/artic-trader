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
  "var(--color-accent-warm)",
  "var(--color-teal)",
  "var(--color-blue-accent)",
  "var(--color-amber)",
]

const TOTAL_KEY = "__total"
const TOTAL_COLOR = "#F2F0EB"
const MAX_RENDERED_POINTS = 600

interface Point {
  t: number // epoch ms (X axis)
  label: string // ISO-ish human tick
  [agentKey: string]: number | string
}

interface SamplePoint {
  index: number
  t: number
  total: number
}

export interface PnlChartProps {
  agents: readonly DemoAgent[]
  trades: readonly DemoTrade[]
  height?: number
}

export interface PnlChartCardProps {
  agent: DemoAgent | null | undefined
  trades: readonly DemoTrade[] // remove single-trade union
  height?: number
  /** Hide axes + grid + reference line. Intended for in-card sparklines. */
  minimal?: boolean
  /** Override the series stroke + gradient colour (useful to mirror PnL sign). */
  color?: string
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
        className="bg-transparent flex items-center justify-center text-sm text-foreground/45"
        style={{ height }}
      >
        Not enough closed trades yet to plot.
      </div>
    )
  }

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="95%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            {agentKeys.map((a, i) => {
              const color = SERIES_COLORS[i % SERIES_COLORS.length]
              return (
                <linearGradient id={`g-${a.id}`} key={a.id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.1} />
                </linearGradient>
              )
            })}
          </defs>

          <CartesianGrid stroke="rgba(194,203,212,0.08)" vertical={false} />

          <XAxis
            dataKey="label"
            stroke="rgba(194,203,212,0.45)"
            tick={{ fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            minTickGap={32}
          />
          <YAxis
            stroke="rgba(194,203,212,0.45)"
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
            stroke="rgba(194,203,212,0.28)"
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
                strokeWidth={3}
                fill={`url(#g-${a.id})`}
                isAnimationActive={false}
                connectNulls
              />
            )
          })}

          {/* Total line — stroke-only so the agent areas stay legible. Rendered
              last so it sits on top. */}
          <Area
            type="monotone"
            dataKey={TOTAL_KEY}
            name="Total"
            stroke={TOTAL_COLOR}
            strokeWidth={1}
            strokeDasharray="8 5"
            fill="transparent"
            dot={false}
            activeDot={{ r: 3.5, fill: TOTAL_COLOR, stroke: TOTAL_COLOR }}
            isAnimationActive={false}
          />
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
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[2px] w-5"
            style={{
              background:
                "repeating-linear-gradient(90deg, #F2F0EB 0 4px, transparent 4px 7px)",
            }}
          />
          <span className="font-semibold text-foreground">Total</span>
        </div>
      </div>
    </div>
  )
}

export function PnlChartCard({
  agent,
  trades,
  height = 300,
  minimal = false,
  color,
}: PnlChartCardProps) {
  // Hooks must run on every render — guard against a null agent inside the
  // memo body, not with an early return above it.
  const { data, agentKeys } = useMemo(() => {
    if (!agent) return { data: [] as Point[], agentKeys: [] as { id: string; name: string; symbol: string }[] }
    const scoped = trades.filter((t) => t.agent_id === agent.id)
    return build([agent], scoped)
  }, [agent, trades])

  if (!agent) {
    return <EmptyState height={height} label="Agent missing." />
  }
  if (data.length <= 1) {
    return <EmptyState height={height} label="Not enough closed trades yet to plot." />
  }

  // Stroke reflects agent's cumulative PnL sign when no explicit color is
  // passed — positive = teal, negative = red-light, flat = warm accent.
  const lastValue = (data[data.length - 1]?.[agent.id] ?? 0) as number
  const autoStroke =
    lastValue > 0.001
      ? "#6FCAA0"
      : lastValue < -0.001
        ? "#F07A6D"
        : "#E8A27A"
  const stroke = color ?? autoStroke
  const gradientId = `g-card-${agent.id}`

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={
            minimal
              ? { top: 0, right: 0, left: 0, bottom: 0 }
              : { top: 8, right: 16, left: 0, bottom: 0 }
          }
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity={0.45} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0} />
            </linearGradient>
          </defs>

          {!minimal && (
            <>
              <CartesianGrid stroke="rgba(194,203,212,0.08)" vertical={false} />
              <XAxis
                dataKey="label"
                stroke="rgba(194,203,212,0.45)"
                tick={{ fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                minTickGap={32}
              />
              <YAxis
                stroke="rgba(194,203,212,0.45)"
                tick={{ fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={44}
                tickFormatter={(v: number) => (v > 0 ? `+${v.toFixed(0)}` : v.toFixed(0))}
              />
              <ReferenceLine y={0} stroke="rgba(194,203,212,0.28)" strokeDasharray="3 3" />
              <Tooltip content={<PnlTooltip agents={agentKeys} />} />
            </>
          )}

          {agentKeys.map((a) => (
            <Area
              key={a.id}
              type="monotone"
              dataKey={a.id}
              name={a.name}
              stroke={stroke}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function EmptyState({ height, label }: { height: number; label: string }) {
  return (
    <div
      className="flex items-center justify-center text-sm text-foreground/45"
      style={{ height }}
    >
      {label}
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function build(
  agents: readonly (DemoAgent | null | undefined)[],
  trades: readonly DemoTrade[],
) {
  const agentKeys = agents
    .filter((a): a is DemoAgent => Boolean(a))
    .map((a) => ({ id: a.id, name: a.name, symbol: a.symbol }))

  if (agentKeys.length === 0) {
    return { data: [], agentKeys }
  }

  const closed = trades
    .filter((t) => t.pnl != null && t.closed_at)
    .sort((a, b) => a.closed_at!.localeCompare(b.closed_at!))

  if (closed.length === 0) {
    return { data: [], agentKeys }
  }

  const startTs = new Date(closed[0].closed_at!).getTime() - 1
  const agentIdSet = new Set(agentKeys.map((a) => a.id))
  const samplePoints: SamplePoint[] = [{ index: 0, t: startTs, total: 0 }]

  let runningTotal = 0
  for (let i = 0; i < closed.length; i++) {
    const tr = closed[i]
    if (agentIdSet.has(tr.agent_id)) {
      runningTotal += tr.pnl as number
    }
    samplePoints.push({
      index: i + 1,
      t: new Date(tr.closed_at!).getTime(),
      total: runningTotal,
    })
  }

  const selectedIndexes = selectLttbIndexes(samplePoints, MAX_RENDERED_POINTS)
  const currentValues: Record<string, number> = {}
  for (const agent of agentKeys) {
    currentValues[agent.id] = 0
  }

  const data: Point[] = []
  runningTotal = 0

  if (selectedIndexes.has(0)) {
    data.push({
      t: startTs,
      label: fmtTick(new Date(startTs)),
      ...currentValues,
      [TOTAL_KEY]: 0,
    })
  }

  for (let i = 0; i < closed.length; i++) {
    const tr = closed[i]
    if (agentIdSet.has(tr.agent_id)) {
      const pnl = tr.pnl as number
      currentValues[tr.agent_id] = (currentValues[tr.agent_id] ?? 0) + pnl
      runningTotal += pnl
    }

    const sampleIndex = i + 1
    if (selectedIndexes.has(sampleIndex)) {
      const closedAt = new Date(tr.closed_at!)
      data.push({
        t: closedAt.getTime(),
        label: fmtTick(closedAt),
        ...currentValues,
        [TOTAL_KEY]: runningTotal,
      })
    }
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

function selectLttbIndexes(points: SamplePoint[], threshold: number): Set<number> {
  if (threshold >= points.length || threshold < 3) {
    return new Set(points.map((point) => point.index))
  }

  const sampled = new Set<number>([points[0].index])
  const bucketSize = (points.length - 2) / (threshold - 2)
  let anchorIndex = 0

  for (let i = 0; i < threshold - 2; i++) {
    const avgStart = Math.floor((i + 1) * bucketSize) + 1
    const avgEnd = Math.min(Math.floor((i + 2) * bucketSize) + 1, points.length)
    const avgLength = avgEnd - avgStart

    let avgT = 0
    let avgTotal = 0
    for (let j = avgStart; j < avgEnd; j++) {
      avgT += points[j].t
      avgTotal += points[j].total
    }
    avgT /= avgLength || 1
    avgTotal /= avgLength || 1

    const rangeStart = Math.floor(i * bucketSize) + 1
    const rangeEnd = Math.min(Math.floor((i + 1) * bucketSize) + 1, points.length - 1)
    const anchor = points[anchorIndex]
    const anchorTotal = anchor.total
    let nextAnchor = points[rangeStart]
    let maxArea = -1

    for (let j = rangeStart; j < rangeEnd; j++) {
      const candidate = points[j]
      const area = Math.abs(
        (anchor.t - avgT) * (candidate.total - anchorTotal) -
          (anchor.t - candidate.t) * (avgTotal - anchorTotal),
      )
      if (area > maxArea) {
        maxArea = area
        nextAnchor = candidate
        anchorIndex = j
      }
    }

    sampled.add(nextAnchor.index)
  }

  sampled.add(points[points.length - 1].index)
  return sampled
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
  // Split total from per-agent rows so it doesn't double-count in the sum
  // and always renders as the emphasis line.
  const totalRow = payload.find((p) => p.dataKey === TOTAL_KEY)
  const agentRows = payload.filter((p) => p.dataKey !== TOTAL_KEY)

  const rows = agentRows
    .map((p: TooltipPayloadRow) => ({
      id: String(p.dataKey),
      name: agents.find((a) => a.id === p.dataKey)?.name ?? "?",
      value: Number(p.value ?? 0),
      color: p.color ?? "#fff",
    }))
    .sort((a: { value: number }, b: { value: number }) => b.value - a.value)

  const total = Number(totalRow?.value ?? rows.reduce((s, r) => s + r.value, 0))

  return (
    <div className="rounded-lg bg-[var(--color-surface-raised)] p-3 shadow-[0_12px_32px_-12px_rgba(0,0,0,0.7)]">
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
        <li className="mt-1.5 flex items-center gap-3 border-t border-[rgba(194,203,212,0.08)] pt-1.5">
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
