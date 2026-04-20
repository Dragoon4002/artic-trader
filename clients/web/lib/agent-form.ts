/**
 * Source of truth for the create-agent form. Mirrors hub/agents/router.py's
 * CreateAgentRequest field set one-to-one — any new hub field shows up here
 * first.
 */

export const SYMBOLS = [
  "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
  "UNI", "ATOM", "LTC", "NEAR", "APT", "ARB", "OP", "SUI", "INJ", "AAVE",
  "FIL", "PEPE", "POL", "BCH", "ETC", "XLM", "HBAR",
] as const
export type Symbol = (typeof SYMBOLS)[number]

export const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"] as const
export type Timeframe = (typeof TIMEFRAMES)[number]

export const RISK_PROFILES = ["conservative", "moderate", "aggressive"] as const
export type RiskProfile = (typeof RISK_PROFILES)[number]

export const TP_SL_MODES = ["fixed", "dynamic"] as const
export type TpSlMode = (typeof TP_SL_MODES)[number]

export const LLM_PROVIDERS = ["anthropic", "openai", "deepseek", "gemini"] as const
export type LlmProvider = (typeof LLM_PROVIDERS)[number]

/** Suggested models per provider. Model id is free-text on submit. */
export const LLM_MODELS: Record<LlmProvider, string[]> = {
  anthropic: ["claude-sonnet-4-5", "claude-3-5-sonnet", "claude-3-5-haiku"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  deepseek: ["deepseek-chat", "deepseek-reasoner", "deepseek-r1"],
  gemini: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
}

export interface AgentFormState {
  // Identity
  name: string
  symbol: Symbol | string
  // Trading
  amount_usdt: number
  leverage: number
  risk_profile: RiskProfile
  primary_timeframe: Timeframe
  poll_seconds: number
  // Risk
  tp_pct: string // kept as string to allow empty → null
  sl_pct: string
  tp_sl_mode: TpSlMode
  max_session_loss_pct: number
  supervisor_interval: number
  // LLM
  llm_provider: LlmProvider
  llm_model: string
  llm_api_key: string
  // Behavior
  live_mode: boolean // alpha-locked false
  auto_start: boolean
}

export const defaultAgentForm: AgentFormState = {
  name: "",
  symbol: "BTC",
  amount_usdt: 100,
  leverage: 5,
  risk_profile: "moderate",
  primary_timeframe: "15m",
  poll_seconds: 1.0,
  tp_pct: "",
  sl_pct: "",
  tp_sl_mode: "fixed",
  max_session_loss_pct: 0.1,
  supervisor_interval: 60,
  llm_provider: "anthropic",
  llm_model: "claude-sonnet-4-5",
  llm_api_key: "",
  live_mode: false,
  auto_start: true,
}

/** Canonicalize form state into the POST /api/agents body. */
export function toCreatePayload(f: AgentFormState) {
  const toNum = (s: string) => (s.trim() === "" ? null : Number(s))
  return {
    name: f.name.trim() || "Unnamed Agent",
    symbol: `${f.symbol}USDT`,
    amount_usdt: f.amount_usdt,
    leverage: f.leverage,
    risk_profile: f.risk_profile,
    primary_timeframe: f.primary_timeframe,
    poll_seconds: f.poll_seconds,
    tp_pct: toNum(f.tp_pct),
    sl_pct: toNum(f.sl_pct),
    tp_sl_mode: f.tp_sl_mode,
    supervisor_interval: f.supervisor_interval,
    live_mode: f.live_mode,
    max_session_loss_pct: f.max_session_loss_pct,
    llm_provider: f.llm_provider,
    llm_model: f.llm_model.trim() || null,
    llm_api_key: f.llm_api_key.trim() || null,
    auto_start: f.auto_start,
  }
}
