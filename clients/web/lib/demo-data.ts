/**
 * Demo fixtures for the dashboard skeleton. Every page that shows "data"
 * pulls from here until the hub session is wired. A single source so the
 * switch-over is one import replacement per page.
 *
 * WARNING: do not treat any value here as real. All agents, prices, txs,
 * ledger entries, and session rows are synthetic.
 */

export type AgentStatus = "alive" | "stopped" | "starting" | "error" | "halted"

export interface DemoAgent {
  id: string
  name: string
  symbol: string
  status: AgentStatus
  price: number
  side: "long" | "short" | "flat"
  amount_usdt: number
  leverage: number
  unrealised_pnl: number | null
  strategy: string
  llm_provider: string
  llm_model: string
  poll_seconds: number
  supervisor_interval: number
  tp_pct: number | null
  sl_pct: number | null
  created_at: string
}

export const demoAgents: DemoAgent[] = [
  {
    id: "a1c9f3d2-11aa-4b5f-8c27-001",
    name: "BTC momentum",
    symbol: "BTCUSDT",
    status: "alive",
    price: 62_841.2,
    side: "long",
    amount_usdt: 500,
    leverage: 5,
    unrealised_pnl: 42.31,
    strategy: "ema_crossover",
    llm_provider: "anthropic",
    llm_model: "claude-sonnet-4-6",
    poll_seconds: 1,
    supervisor_interval: 60,
    tp_pct: 1.5,
    sl_pct: 0.8,
    created_at: "2026-04-18T10:22:11Z",
  },
  {
    id: "b2e8d1c7-22bb-4c6e-9d38-002",
    name: "ETH fade",
    symbol: "ETHUSDT",
    status: "alive",
    price: 3_041.55,
    side: "short",
    amount_usdt: 300,
    leverage: 3,
    unrealised_pnl: -7.82,
    strategy: "rsi_reversion",
    llm_provider: "openai",
    llm_model: "gpt-5",
    poll_seconds: 1,
    supervisor_interval: 90,
    tp_pct: 0.9,
    sl_pct: 1.2,
    created_at: "2026-04-19T02:44:03Z",
  },
  {
    id: "c3fa2b06-33cc-4d7f-ae49-003",
    name: "SOL breakout",
    symbol: "SOLUSDT",
    status: "stopped",
    price: 148.27,
    side: "flat",
    amount_usdt: 200,
    leverage: 2,
    unrealised_pnl: null,
    strategy: "atr_breakout",
    llm_provider: "anthropic",
    llm_model: "claude-haiku-4-5",
    poll_seconds: 2,
    supervisor_interval: 120,
    tp_pct: 2.0,
    sl_pct: 1.0,
    created_at: "2026-04-15T18:05:40Z",
  },
  {
    id: "d4fb3c15-44dd-4e80-bf50-004",
    name: "BNB scalp",
    symbol: "BNBUSDT",
    status: "halted",
    price: 578.91,
    side: "flat",
    amount_usdt: 150,
    leverage: 4,
    unrealised_pnl: null,
    strategy: "vwap_meanrev",
    llm_provider: "deepseek",
    llm_model: "deepseek-r1",
    poll_seconds: 1,
    supervisor_interval: 60,
    tp_pct: 0.6,
    sl_pct: 0.4,
    created_at: "2026-04-20T06:12:00Z",
  },
]

export function findDemoAgent(id: string): DemoAgent | undefined {
  return demoAgents.find((a) => a.id === id || a.id.startsWith(id))
}

export interface DemoTrade {
  id: string
  agent_id: string
  side: "long" | "short"
  entry_price: number
  exit_price: number | null
  size_usdt: number
  leverage: number
  pnl: number | null
  strategy: string
  close_reason: "TP" | "SL" | "SUPERVISOR" | "MANUAL" | null
  opened_at: string
  closed_at: string | null
}

export const demoTrades: DemoTrade[] = [
  // ── BTC agent — ema_crossover ─────────────────────────────────────
  { id: "t1", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "long",  entry_price: 61_210.0, exit_price: 61_020.0, size_usdt: 500, leverage: 5, pnl:  -7.76, strategy: "ema_crossover", close_reason: "SL",         opened_at: "2026-04-18T09:02:14Z", closed_at: "2026-04-18T10:20:02Z" },
  { id: "t2", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "long",  entry_price: 61_500.0, exit_price: 61_902.0, size_usdt: 500, leverage: 5, pnl:  16.34, strategy: "ema_crossover", close_reason: "TP",         opened_at: "2026-04-18T14:40:00Z", closed_at: "2026-04-18T16:10:20Z" },
  { id: "t3", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "short", entry_price: 63_100.0, exit_price: 63_280.5, size_usdt: 500, leverage: 5, pnl:  -7.15, strategy: "ema_crossover", close_reason: "SL",         opened_at: "2026-04-19T14:02:45Z", closed_at: "2026-04-19T14:38:12Z" },
  { id: "t4", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "long",  entry_price: 61_940.0, exit_price: 62_241.3, size_usdt: 500, leverage: 5, pnl:  12.14, strategy: "ema_crossover", close_reason: "SUPERVISOR", opened_at: "2026-04-19T22:10:03Z", closed_at: "2026-04-19T23:47:00Z" },
  { id: "t5", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "long",  entry_price: 62_410.5, exit_price: 62_840.8, size_usdt: 500, leverage: 5, pnl:  17.24, strategy: "ema_crossover", close_reason: "TP",         opened_at: "2026-04-20T09:31:12Z", closed_at: "2026-04-20T11:05:44Z" },
  // Open position (no close yet)
  { id: "t6", agent_id: "a1c9f3d2-11aa-4b5f-8c27-001", side: "long",  entry_price: 62_630.0, exit_price: null,     size_usdt: 500, leverage: 5, pnl:  null,  strategy: "ema_crossover", close_reason: null,         opened_at: "2026-04-20T12:14:09Z", closed_at: null },

  // ── ETH agent — rsi_reversion (net negative) ──────────────────────
  { id: "e1", agent_id: "b2e8d1c7-22bb-4c6e-9d38-002", side: "short", entry_price: 3_120.0,  exit_price: 3_088.0,  size_usdt: 300, leverage: 3, pnl:   9.23, strategy: "rsi_reversion", close_reason: "TP",         opened_at: "2026-04-18T11:05:00Z", closed_at: "2026-04-18T12:55:14Z" },
  { id: "e2", agent_id: "b2e8d1c7-22bb-4c6e-9d38-002", side: "long",  entry_price: 3_068.0,  exit_price: 3_012.0,  size_usdt: 300, leverage: 3, pnl: -16.44, strategy: "rsi_reversion", close_reason: "SL",         opened_at: "2026-04-18T20:20:00Z", closed_at: "2026-04-18T21:44:41Z" },
  { id: "e3", agent_id: "b2e8d1c7-22bb-4c6e-9d38-002", side: "short", entry_price: 3_095.0,  exit_price: 3_121.0,  size_usdt: 300, leverage: 3, pnl:  -7.55, strategy: "rsi_reversion", close_reason: "SUPERVISOR", opened_at: "2026-04-19T08:15:00Z", closed_at: "2026-04-19T09:40:00Z" },
  { id: "e4", agent_id: "b2e8d1c7-22bb-4c6e-9d38-002", side: "long",  entry_price: 3_010.0,  exit_price: 3_044.0,  size_usdt: 300, leverage: 3, pnl:  10.16, strategy: "rsi_reversion", close_reason: "TP",         opened_at: "2026-04-19T16:30:22Z", closed_at: "2026-04-19T17:55:10Z" },
  // Open short
  { id: "e5", agent_id: "b2e8d1c7-22bb-4c6e-9d38-002", side: "short", entry_price: 3_051.0,  exit_price: null,     size_usdt: 300, leverage: 3, pnl:  null,  strategy: "rsi_reversion", close_reason: null,         opened_at: "2026-04-20T10:10:00Z", closed_at: null },

  // ── SOL agent — atr_breakout (net positive) ───────────────────────
  { id: "s1", agent_id: "c3fa2b06-33cc-4d7f-ae49-003", side: "long",  entry_price: 142.10,   exit_price: 145.20,   size_usdt: 200, leverage: 2, pnl:   8.72, strategy: "atr_breakout",  close_reason: "TP",         opened_at: "2026-04-17T19:12:00Z", closed_at: "2026-04-17T22:05:00Z" },
  { id: "s2", agent_id: "c3fa2b06-33cc-4d7f-ae49-003", side: "long",  entry_price: 144.80,   exit_price: 143.55,   size_usdt: 200, leverage: 2, pnl:  -3.45, strategy: "atr_breakout",  close_reason: "SUPERVISOR", opened_at: "2026-04-18T05:30:00Z", closed_at: "2026-04-18T07:00:00Z" },
  { id: "s3", agent_id: "c3fa2b06-33cc-4d7f-ae49-003", side: "long",  entry_price: 143.90,   exit_price: 148.00,   size_usdt: 200, leverage: 2, pnl:  11.40, strategy: "atr_breakout",  close_reason: "TP",         opened_at: "2026-04-19T11:00:00Z", closed_at: "2026-04-19T15:20:00Z" },

  // ── BNB agent — vwap_meanrev (halted, net negative: why credits halted) ─
  { id: "n1", agent_id: "d4fb3c15-44dd-4e80-bf50-004", side: "short", entry_price: 584.00,   exit_price: 581.00,   size_usdt: 150, leverage: 4, pnl:   3.08, strategy: "vwap_meanrev",  close_reason: "TP",         opened_at: "2026-04-19T23:05:00Z", closed_at: "2026-04-20T01:40:00Z" },
  { id: "n2", agent_id: "d4fb3c15-44dd-4e80-bf50-004", side: "long",  entry_price: 580.00,   exit_price: 573.50,   size_usdt: 150, leverage: 4, pnl:  -6.72, strategy: "vwap_meanrev",  close_reason: "SL",         opened_at: "2026-04-20T02:30:00Z", closed_at: "2026-04-20T03:20:00Z" },
  { id: "n3", agent_id: "d4fb3c15-44dd-4e80-bf50-004", side: "long",  entry_price: 575.00,   exit_price: 570.10,   size_usdt: 150, leverage: 4, pnl:  -5.11, strategy: "vwap_meanrev",  close_reason: "SL",         opened_at: "2026-04-20T04:05:00Z", closed_at: "2026-04-20T05:12:00Z" },
]

export interface DemoLog {
  level: "init" | "llm" | "tick" | "action" | "sl_tp" | "supervisor" | "warn" | "error"
  message: string
  timestamp: string
}

export const demoLogs: DemoLog[] = [
  { level: "init", timestamp: "12:14:09", message: "Agent started for BTCUSDT @ 62630.00" },
  { level: "llm", timestamp: "12:14:10", message: "LLMPlanner → strategy=ema_crossover threshold=0.6 lookback=20" },
  { level: "tick", timestamp: "12:14:11", message: "price=62631.50 signal=0.42 position=flat" },
  { level: "tick", timestamp: "12:14:12", message: "price=62634.00 signal=0.61 position=flat" },
  { level: "action", timestamp: "12:14:12", message: "OPEN LONG 500 USDT @ 62634.00 leverage=5 tp=1.5% sl=0.8%" },
  { level: "tick", timestamp: "12:14:13", message: "price=62641.00 unrealised=+11.18 USDT" },
  { level: "tick", timestamp: "12:14:14", message: "price=62648.00 unrealised=+22.36 USDT" },
  { level: "supervisor", timestamp: "12:15:12", message: "KEEP — position aligned with 1h trend" },
  { level: "tick", timestamp: "12:15:13", message: "price=62841.20 unrealised=+42.31 USDT" },
  { level: "warn", timestamp: "12:15:30", message: "Pyth feed lag 240ms (threshold 200ms)" },
]

// ── Strategies ──────────────────────────────────────────────────────────────

export interface DemoStrategy {
  id: string
  name: string
  source: "builtin" | "marketplace" | "authored"
  description: string
  installs?: number
  author?: string
  updated_at?: string
}

export const demoInstalledStrategies: DemoStrategy[] = [
  // ── momentum ──────────────────────────────────────────────────────────────
  { id: "simple_momentum", name: "simple_momentum", source: "builtin", description: "Basic price-vs-N-bars-ago momentum signal. The fallback when authored strategies fail." },
  { id: "dual_momentum", name: "dual_momentum", source: "builtin", description: "Combined absolute + relative momentum across two lookback windows." },
  { id: "breakout", name: "breakout", source: "builtin", description: "Range breakout above/below recent N-bar high/low." },
  { id: "donchian_channel", name: "donchian_channel", source: "builtin", description: "20-bar Donchian channel breakout — canonical Turtle entry." },
  { id: "ma_crossover", name: "ma_crossover", source: "builtin", description: "Simple moving-average crossover (fast/slow SMA)." },
  { id: "ema_crossover", name: "ema_crossover", source: "builtin", description: "Classic 12/26 EMA crossover with zero-lag entry confirmation." },
  { id: "macd_signal", name: "macd_signal", source: "builtin", description: "MACD line vs signal line with histogram momentum." },
  { id: "adx_filter", name: "adx_filter", source: "builtin", description: "ADX(14) trend-strength gate — only fires above threshold." },
  { id: "supertrend", name: "supertrend", source: "builtin", description: "Supertrend(10, 3) directional bias on ATR bands." },
  { id: "ichimoku_signal", name: "ichimoku_signal", source: "builtin", description: "Ichimoku cloud + Tenkan/Kijun cross signal." },
  // ── mean reversion ────────────────────────────────────────────────────────
  { id: "z_score", name: "z_score", source: "builtin", description: "Rolling z-score reversion against the N-bar mean." },
  { id: "bollinger_reversion", name: "bollinger_reversion", source: "builtin", description: "Fade outer Bollinger bands back to the 20-SMA midline." },
  { id: "rsi_signal", name: "rsi_signal", source: "builtin", description: "RSI(14) reversion on >70 / <30 extremes." },
  { id: "stochastic_signal", name: "stochastic_signal", source: "builtin", description: "Stochastic %K/%D oversold/overbought crossover." },
  { id: "range_sr", name: "range_sr", source: "builtin", description: "Support/resistance bounce inside detected price range." },
  // ── volatility ────────────────────────────────────────────────────────────
  { id: "atr_breakout", name: "atr_breakout", source: "builtin", description: "ATR-band breakout with volume confirmation." },
  { id: "bollinger_squeeze", name: "bollinger_squeeze", source: "builtin", description: "Detect Bollinger squeeze and trade the expansion direction." },
  { id: "keltner_bollinger", name: "keltner_bollinger", source: "builtin", description: "Keltner-vs-Bollinger band-width regime filter." },
  // ── volume ────────────────────────────────────────────────────────────────
  { id: "vwap_deviation", name: "vwap_deviation", source: "builtin", description: "Mean-revert on price deviation from session VWAP." },
  { id: "obv_trend", name: "obv_trend", source: "builtin", description: "On-Balance-Volume slope as trend confirmation." },
  { id: "funding_bias_stub", name: "funding_bias_stub", source: "builtin", description: "Perp funding-rate bias signal (stub — feed wiring pending)." },
  // ── statistical ───────────────────────────────────────────────────────────
  { id: "linear_regression_channel", name: "linear_regression_channel", source: "builtin", description: "Linear-regression channel mean-reversion against ±2σ bands." },
  { id: "kalman_fair_value", name: "kalman_fair_value", source: "builtin", description: "Kalman-filter fair-value estimate; trade deviations from it." },
  // ── risk sizing ───────────────────────────────────────────────────────────
  { id: "kelly_size", name: "kelly_size", source: "builtin", description: "Fractional-Kelly position sizing from win-rate/payoff estimates." },
  { id: "vol_scaling_mult", name: "vol_scaling_mult", source: "builtin", description: "Inverse-volatility size multiplier — caps risk per tick." },
  // ── time filters ──────────────────────────────────────────────────────────
  { id: "session_filter", name: "session_filter", source: "builtin", description: "Trade only inside configured UTC session windows." },
  { id: "day_of_week_filter", name: "day_of_week_filter", source: "builtin", description: "Skip configured weekdays (e.g. illiquid weekends)." },
  // ── marketplace fork ──────────────────────────────────────────────────────
  {
    id: "vwap_meanrev_v2",
    name: "vwap_meanrev_v2",
    source: "marketplace",
    description: "Community fork of vwap_meanrev with session-aware bands.",
    author: "alice.init",
  },
]

export const demoAuthoredStrategies: DemoStrategy[] = [
  {
    id: "my_trend_scalp",
    name: "my_trend_scalp",
    source: "authored",
    description: "Personal scalp using Donchian channel + RSI filter. Needs more testing.",
    updated_at: "2026-04-17T22:44:01Z",
  },
]

// ── Marketplace ─────────────────────────────────────────────────────────────

export interface DemoMarketplaceItem {
  id: string
  name: string
  description: string
  author: string
  installs: number
  reports: number
  created_at: string
  code_preview: string
}

export const demoMarketplace: DemoMarketplaceItem[] = [
  {
    id: "vwap_meanrev_v2",
    name: "vwap_meanrev_v2",
    description: "Community fork of vwap_meanrev with session-aware bands and reduced whipsaw on low-vol days.",
    author: "alice.init",
    installs: 412,
    reports: 0,
    created_at: "2026-03-22T09:12:40Z",
    code_preview: `def strategy(plan, price_history, candles):
    # vwap_meanrev_v2 — session-aware VWAP mean reversion
    vwap = sum(c['close'] * c['volume'] for c in candles) / sum(c['volume'] for c in candles)
    price = price_history[-1]
    band = plan.get('band_bps', 40) / 10_000
    if price > vwap * (1 + band):
        return -1.0, 'fade upper band'
    if price < vwap * (1 - band):
        return 1.0, 'fade lower band'
    return 0.0, 'in band'
`,
  },
  {
    id: "donchian_breakout",
    name: "donchian_breakout",
    description: "20-bar Donchian breakout with trailing stop on the opposite band. Canonical Turtle-style entry.",
    author: "bob.init",
    installs: 318,
    reports: 1,
    created_at: "2026-03-29T16:31:02Z",
    code_preview: `def strategy(plan, price_history, candles):
    # donchian_breakout — long above 20-bar high, short below 20-bar low
    highs = [c['high'] for c in candles[-20:]]
    lows  = [c['low']  for c in candles[-20:]]
    price = price_history[-1]
    if price >= max(highs): return 1.0, '20-bar high breakout'
    if price <= min(lows):  return -1.0, '20-bar low breakdown'
    return 0.0, 'range-bound'
`,
  },
  {
    id: "supertrend_filter",
    name: "supertrend_filter",
    description: "Supertrend(10, 3) bias filter on top of an EMA cross. Keeps you out of chop.",
    author: "carol.init",
    installs: 187,
    reports: 0,
    created_at: "2026-04-02T21:04:55Z",
    code_preview: `def strategy(plan, price_history, candles):
    # supertrend_filter — trade only in direction of supertrend
    atr = sum(c['high'] - c['low'] for c in candles[-10:]) / 10
    upper = candles[-1]['close'] + 3 * atr
    lower = candles[-1]['close'] - 3 * atr
    price = price_history[-1]
    trend = 1 if price > lower else -1 if price < upper else 0
    return 0.5 * trend, f'supertrend={trend}'
`,
  },
  {
    id: "orderflow_imbalance",
    name: "orderflow_imbalance",
    description: "Volume-delta tilt over rolling 5 candles. Signals when buy vs sell flow diverges from price.",
    author: "dave.init",
    installs: 94,
    reports: 3,
    created_at: "2026-04-11T04:55:11Z",
    code_preview: `def strategy(plan, price_history, candles):
    # orderflow_imbalance — rolling delta volume
    delta = sum(1 if c['close'] >= c['open'] else -1 for c in candles[-5:])
    return delta / 5, f'delta={delta}'
`,
  },
]

export function findDemoMarketplace(id: string): DemoMarketplaceItem | undefined {
  return demoMarketplace.find((m) => m.id === id)
}

// ── Credits ─────────────────────────────────────────────────────────────────

export const demoCreditBalance = 42.73

export interface DemoLedgerRow {
  id: string
  delta: number
  reason: "tick_debit" | "admin_grant" | "halt_refund"
  agent_id?: string
  created_at: string
}

export const demoLedger: DemoLedgerRow[] = [
  { id: "l1", delta: -0.033, reason: "tick_debit", agent_id: "a1c9f3d2", created_at: "2026-04-20T12:15:00Z" },
  { id: "l2", delta: -0.033, reason: "tick_debit", agent_id: "b2e8d1c7", created_at: "2026-04-20T12:15:00Z" },
  { id: "l3", delta: -0.033, reason: "tick_debit", agent_id: "a1c9f3d2", created_at: "2026-04-20T12:14:00Z" },
  { id: "l4", delta: -0.033, reason: "tick_debit", agent_id: "b2e8d1c7", created_at: "2026-04-20T12:14:00Z" },
  { id: "l5", delta: +50, reason: "admin_grant", created_at: "2026-04-19T09:00:00Z" },
  { id: "l6", delta: -0.033, reason: "tick_debit", agent_id: "a1c9f3d2", created_at: "2026-04-19T08:59:00Z" },
  { id: "l7", delta: +0.4, reason: "halt_refund", created_at: "2026-04-18T22:00:00Z" },
]

// ── Indexer ────────────────────────────────────────────────────────────────

export interface DemoIndexerRow {
  tx_hash: string
  agent_id: string
  kind: "trades" | "supervise"
  amount_usdt: number | null
  symbol: string
  side?: "long" | "short"
  block: number
  created_at: string
}

export const demoIndexer: DemoIndexerRow[] = [
  { tx_hash: "0xa1f3…9c4e", agent_id: "a1c9f3d2", kind: "trades", amount_usdt: 500, symbol: "BTCUSDT", side: "long", block: 14_281_001, created_at: "2026-04-20T12:14:12Z" },
  { tx_hash: "0x7b22…22a8", agent_id: "a1c9f3d2", kind: "supervise", amount_usdt: null, symbol: "BTCUSDT", block: 14_280_920, created_at: "2026-04-20T12:05:01Z" },
  { tx_hash: "0x4c90…71df", agent_id: "b2e8d1c7", kind: "trades", amount_usdt: 300, symbol: "ETHUSDT", side: "short", block: 14_280_744, created_at: "2026-04-20T11:40:55Z" },
  { tx_hash: "0x2e11…0b33", agent_id: "a1c9f3d2", kind: "trades", amount_usdt: 500, symbol: "BTCUSDT", side: "long", block: 14_280_020, created_at: "2026-04-20T11:05:44Z" },
  { tx_hash: "0x8f03…ab12", agent_id: "b2e8d1c7", kind: "supervise", amount_usdt: null, symbol: "ETHUSDT", block: 14_279_914, created_at: "2026-04-20T10:55:30Z" },
]

// ── Settings ───────────────────────────────────────────────────────────────

export interface DemoSessionKey {
  session_id: string
  scope: string
  created_at: string
  expires_at: string
  last_used_at: string
  ua_hint: string
}

export const demoSessionKeys: DemoSessionKey[] = [
  {
    session_id: "sess_9c1a…bd44",
    scope: "authenticated-actions",
    created_at: "2026-04-20T08:02:11Z",
    expires_at: "2026-04-20T16:02:11Z",
    last_used_at: "2026-04-20T12:15:02Z",
    ua_hint: "Firefox · Linux (this tab)",
  },
  {
    session_id: "sess_2f84…aa10",
    scope: "authenticated-actions",
    created_at: "2026-04-19T22:44:00Z",
    expires_at: "2026-04-20T06:44:00Z",
    last_used_at: "2026-04-20T03:01:09Z",
    ua_hint: "Safari · iPhone",
  },
]

export const demoApiKeyHint = "artic_•••••••••••••L8kQ"
