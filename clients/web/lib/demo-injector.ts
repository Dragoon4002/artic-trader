/**
 * Deterministic demo-trade injector. Same agent id → same trades on every
 * render. Used to make the dashboard feel populated even when real on-chain
 * activity is sparse.
 *
 * Strategy:
 *   - per agent, generate a fixed number of "closed" trades over the last 36h
 *   - sum of pnl matches `fakeProfitForAgent(id).realised`
 *   - timestamps are jittered so each agent has a unique cadence
 *   - tx_hash is a fake 32-byte hex (NOT on-chain — non-clickable rows)
 */

import type { Trade } from "./schemas"

/** Symbols/names that should render as "real" (flat, no demo PnL injection,
 *  not counted in dashboard totals). The match is case-insensitive prefix on
 *  symbol or name. */
const REAL_AGENT_PATTERNS = ["link"]

export function isFlatAgent(agent: { symbol?: string; name?: string }): boolean {
  const sym = (agent.symbol ?? "").toLowerCase()
  const name = (agent.name ?? "").toLowerCase()
  return REAL_AGENT_PATTERNS.some((p) => sym.startsWith(p) || name.startsWith(p))
}

const TRADE_COUNT = 12
const WINDOW_HOURS = 36
const STRATEGY_POOL = [
  "momentum", "rsi_signal", "macd_signal", "bollinger_reversion",
  "ema_crossover", "supertrend", "z_score", "atr_breakout",
  "vwap_reversion", "ichimoku", "kalman_fair_value", "dual_momentum",
]
const CLOSE_REASONS = ["TP", "SL", "SUPERVISOR", "MANUAL"] as const
const SIDES = ["long", "short"] as const

function hashSeed(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return h >>> 0
}

/** Mulberry32 — deterministic PRNG seeded by `n`. */
function mulberry32(n: number) {
  let t = n
  return function () {
    t = (t + 0x6d2b79f5) | 0
    let r = Math.imul(t ^ (t >>> 15), 1 | t)
    r = r + (Math.imul(r ^ (r >>> 7), 61 | r) ^ r)
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296
  }
}

export function fakeProfitForAgent(agentId: string): {
  realised: number
  unrealised: number
} {
  const rnd = mulberry32(hashSeed(agentId))
  const r1 = rnd() * 2 - 1
  const r2 = rnd() * 2 - 1
  // Bias positive — most agents look profitable
  const biased = r1 < 0 ? r1 * 0.4 : r1
  const realised = Math.round(biased * 13_000 + (r1 >= 0 ? 2_500 : -1_500))
  const unrealised = Math.round(r2 * 3_500)
  return { realised, unrealised }
}

/** Generate N synthetic closed trades for an agent. Sum of pnl ≈ targetTotal. */
export function generateDemoTrades(
  agentId: string,
  agentSymbol: string,
  targetTotal: number,
): Trade[] {
  const rnd = mulberry32(hashSeed(agentId + ":trades"))
  const now = Date.now()

  // Distribute targetTotal across TRADE_COUNT trades with noise. Most rows
  // contribute small amounts; a few are larger winners.
  const weights: number[] = []
  for (let i = 0; i < TRADE_COUNT; i++) {
    weights.push(0.3 + rnd() * 1.7) // 0.3 – 2.0
  }
  // 2 of the trades are "big winners" — boost their weight
  const bigA = Math.floor(rnd() * TRADE_COUNT)
  const bigB = Math.floor(rnd() * TRADE_COUNT)
  weights[bigA] *= 3
  weights[bigB] *= 2.5
  const totalWeight = weights.reduce((a, b) => a + b, 0)

  // 70% of trades are winners (positive pnl), 30% small losers
  const trades: Trade[] = []
  let cumulative = 0
  for (let i = 0; i < TRADE_COUNT; i++) {
    const isWinner = rnd() > 0.3
    const sign = isWinner ? 1 : -0.5
    const allocation = (weights[i] / totalWeight) * targetTotal * sign

    const side = SIDES[Math.floor(rnd() * SIDES.length)]
    const entry = Math.round((0.5 + rnd() * 200) * 1000) / 1000
    const exitPct = (rnd() - 0.4) * 0.08 // ~ -3.2% to +4.8%
    const exit = Math.round(entry * (1 + exitPct) * 1000) / 1000
    const sizeUsdt = [100, 250, 500, 1000, 2500, 5000][Math.floor(rnd() * 6)]
    const leverage = [1, 3, 5, 10][Math.floor(rnd() * 4)]
    const strategy = STRATEGY_POOL[Math.floor(rnd() * STRATEGY_POOL.length)]
    const closeReason = CLOSE_REASONS[Math.floor(rnd() * CLOSE_REASONS.length)]

    // Spread trades across the past WINDOW_HOURS, oldest first
    const minutesAgo = Math.round(((TRADE_COUNT - i) / TRADE_COUNT) * WINDOW_HOURS * 60 + rnd() * 30)
    const closedAt = new Date(now - minutesAgo * 60_000)
    const openedAt = new Date(closedAt.getTime() - (5 + rnd() * 25) * 60_000)

    cumulative += allocation
    const pnl = Math.round(allocation * 100) / 100

    // Fake 32-byte hex tx hash (looks real — DO NOT click)
    const txHash =
      "0x" +
      Array.from({ length: 64 }, () =>
        Math.floor(rnd() * 16).toString(16),
      ).join("")

    trades.push({
      id: `demo-${agentId}-${i}`,
      agent_id: agentId,
      side,
      entry_price: entry,
      exit_price: exit,
      size_usdt: sizeUsdt,
      leverage,
      pnl,
      strategy,
      close_reason: closeReason,
      opened_at: openedAt.toISOString(),
      closed_at: closedAt.toISOString(),
      tx_hash: txHash,
    } as Trade)
  }

  // Tiny correction so the sum lines up with target — adjust the last trade
  if (trades.length > 0) {
    const drift = targetTotal - cumulative
    const last = trades[trades.length - 1]
    if (last.pnl != null) {
      last.pnl = Math.round((last.pnl + drift) * 100) / 100
    }
  }
  return trades
}

/** Produce demo trades for an array of agents. */
export function generateDemoTradesFor(
  agents: { id: string; symbol: string; name?: string }[],
): Trade[] {
  const out: Trade[] = []
  for (const a of agents) {
    if (isFlatAgent(a)) continue // LINK Agent → flat, no fake trades
    const target = fakeProfitForAgent(a.id).realised
    out.push(...generateDemoTrades(a.id, a.symbol, target))
  }
  return out
}
