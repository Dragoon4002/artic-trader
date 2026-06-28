"use client"

import { useMemo } from "react"
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface Point { t: number; label: string; total: number }

const MAX_RENDERED_POINTS = 600

export function PnlAreaChart({
  trades,
  height = 300,
}: {
  trades: readonly { closed_at: string | null; pnl: number | null }[]
  height?: number
}) {
  const data = useMemo<Point[]>(() => {
    const closed = [...trades]
      .filter(t => t.pnl != null && t.closed_at)
      .sort((a, b) => a.closed_at!.localeCompare(b.closed_at!))
    if (!closed.length) return []
    const start = new Date(closed[0].closed_at!).getTime() - 1
    const out: Point[] = [{ t: start, label: fmtTick(new Date(start)), total: 0 }]
    let running = 0
    for (const tr of closed) {
      running += tr.pnl as number
      const ts = new Date(tr.closed_at!).getTime()
      out.push({ t: ts, label: fmtTick(new Date(ts)), total: running })
    }
    return downsampleLttb(out, MAX_RENDERED_POINTS)
  }, [trades])

  if (data.length <= 1) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-sm text-foreground/45">
        Not enough closed trades yet to plot.
      </div>
    )
  }

  const last = data[data.length - 1].total
  const stroke = last > 0.001 ? "#6FCAA0" : last < -0.001 ? "#F07A6D" : "#F3E4D1"

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="g-overview-total" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity={0.5} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(194,203,212,0.08)" vertical={false} />
          <XAxis dataKey="label" stroke="rgba(194,203,212,0.45)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={48} />
          <YAxis stroke="rgba(194,203,212,0.45)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} width={48} tickFormatter={(v: number) => v > 0 ? `+$${v.toFixed(0)}` : `$${v.toFixed(0)}`} />
          <ReferenceLine y={0} stroke="rgba(194,203,212,0.28)" strokeDasharray="3 3" />
          <Tooltip content={<TT />} />
          <Area
            type="monotone"
            dataKey="total"
            stroke={stroke}
            strokeWidth={2.5}
            fill="url(#g-overview-total)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function downsampleLttb(points: Point[], threshold: number): Point[] {
  if (threshold >= points.length || threshold < 3) return points

  const sampled: Point[] = [points[0]]
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
    let nextAnchor = points[rangeStart]
    let maxArea = -1

    for (let j = rangeStart; j < rangeEnd; j++) {
      const candidate = points[j]
      const area = Math.abs(
        (anchor.t - avgT) * (candidate.total - anchor.total) -
          (anchor.t - candidate.t) * (avgTotal - anchor.total),
      )
      if (area > maxArea) {
        maxArea = area
        nextAnchor = candidate
        anchorIndex = j
      }
    }

    sampled.push(nextAnchor)
  }

  sampled.push(points[points.length - 1])
  return sampled
}

function fmtTick(d: Date) {
  const month = d.toLocaleString("en-US", { month: "short", timeZone: "UTC" })
  const day = d.getUTCDate().toString().padStart(2, "0")
  return `${month} ${day}`
}

interface TTProps { active?: boolean; payload?: { value?: number }[]; label?: string | number }
function TT({ active, payload, label }: TTProps) {
  if (!active || !payload?.length) return null
  const v = Number(payload[0].value ?? 0)
  const tone = v > 0 ? "text-[var(--color-teal)]" : v < 0 ? "text-[var(--color-red-light)]" : "text-foreground/60"
  const sign = v > 0 ? "+" : v < 0 ? "-" : ""
  return (
    <div className="rounded-lg bg-[var(--color-surface-raised)] p-3 shadow-[0_12px_32px_-12px_rgba(0,0,0,0.7)]">
      <p className="mb-1 text-[11px] font-mono text-foreground/50">{label}</p>
      <p className={`text-sm font-mono ${tone}`}>{sign}${Math.abs(v).toFixed(2)}</p>
    </div>
  )
}
