/**
 * Typed API client.
 *
 *   WIRED  ── hits hub via signedFetch (JWT from localStorage, populated by useHubAuth)
 *   DEMO   ── returns fixture data until the hub route lands
 *
 * Module status:
 *   WIRED:  agents (list/get/CRUD/start/stop), strategies, trades-from-indexer, secrets
 *   DEMO :  logs, credits, ledger, marketplace, sessions, api-key hint
 *
 * Demo bodies are still here so the dashboard renders during backend work.
 */

import {
  demoApiKeyHint,
  demoCreditBalance,
  demoIndexer,
  demoLedger,
  demoLogs,
  demoMarketplace,
  demoSessionKeys,
} from "./demo-data"
import { signedFetch } from "./signed-fetch"
import type {
  Agent,
  CreateAgentRequest,
  Credits,
  IndexerFilter,
  IndexerRow,
  LedgerRow,
  LogEntry,
  MarketplaceItem,
  MarketplaceSort,
  SessionKey,
  Strategy,
  Trade,
} from "./schemas"

const latency = () => new Promise((r) => setTimeout(r, 120 + Math.random() * 180))

// ── Backend shapes (what hub actually returns) ─────────────────────────────

interface BackendAgent {
  id: string
  name: string
  symbol: string
  llm_provider: string
  llm_model: string
  strategy_pool: string[]
  risk_params: {
    amount_usdt?: number
    leverage?: number
    poll_seconds?: number
    supervisor_interval?: number
    tp_pct?: number | null
    sl_pct?: number | null
  }
  status: string
  container_id: string | null
  port: number | null
  unrealized_pnl_usdt: number | null
  current_strategy: string | null
  created_at: string
  updated_at: string
}

function toClientAgent(b: BackendAgent): Agent {
  return {
    id: b.id,
    name: b.name,
    symbol: b.symbol,
    // Status values from user-server include "stopped" / "alive" / "halted" /
    // "error" — web client's AgentStatus enum is narrower; pass through, Zod
    // parse in consumers will surface mismatches if any.
    status: b.status as Agent["status"],
    price: 0, // live field — not exposed via REST yet
    side: "flat" as Agent["side"],
    amount_usdt: b.risk_params.amount_usdt ?? 0,
    leverage: b.risk_params.leverage ?? 1,
    unrealised_pnl: b.unrealized_pnl_usdt ?? null,
    strategy: b.current_strategy ?? b.strategy_pool[0] ?? "unknown",
    llm_provider: b.llm_provider,
    llm_model: b.llm_model,
    poll_seconds: b.risk_params.poll_seconds ?? 1,
    supervisor_interval: b.risk_params.supervisor_interval ?? 60,
    tp_pct: b.risk_params.tp_pct ?? null,
    sl_pct: b.risk_params.sl_pct ?? null,
    created_at: b.created_at,
  }
}

// ── Agents (WIRED) ─────────────────────────────────────────────────────────

export async function listAgents(): Promise<Agent[]> {
  const rows = await signedFetch<BackendAgent[]>("/api/v1/u/agents")
  return rows.map(toClientAgent)
}

export async function getAgent(id: string): Promise<Agent | null> {
  try {
    const row = await signedFetch<BackendAgent>(`/api/v1/u/agents/${id}`)
    return toClientAgent(row)
  } catch {
    return null
  }
}

export async function createAgent(body: CreateAgentRequest): Promise<Agent> {
  const backendBody = {
    name: body.name,
    symbol: body.symbol,
    llm_provider: body.llm_provider,
    llm_model: body.llm_model,
    strategy_pool: [body.strategy],
    risk_params: {
      amount_usdt: body.amount_usdt,
      leverage: body.leverage,
      poll_seconds: body.poll_seconds,
      supervisor_interval: body.supervisor_interval,
      tp_pct: body.tp_pct ?? null,
      sl_pct: body.sl_pct ?? null,
    },
  }
  const row = await signedFetch<BackendAgent>("/api/v1/u/agents", {
    method: "POST",
    body: backendBody,
  })
  return toClientAgent(row)
}

export async function deleteAgent(id: string): Promise<void> {
  await signedFetch<void>(`/api/v1/u/agents/${id}`, { method: "DELETE" })
}

export async function startAgent(id: string): Promise<Agent> {
  const row = await signedFetch<BackendAgent>(`/api/v1/u/agents/${id}/start`, {
    method: "POST",
  })
  return toClientAgent(row)
}

export async function stopAgent(id: string): Promise<Agent> {
  const row = await signedFetch<BackendAgent>(`/api/v1/u/agents/${id}/stop`, {
    method: "POST",
  })
  return toClientAgent(row)
}

export async function startAllAgents(): Promise<Agent[]> {
  const rows = await signedFetch<BackendAgent[]>("/api/v1/u/agents/start-all", {
    method: "POST",
  })
  return rows.map(toClientAgent)
}

export async function stopAllAgents(): Promise<Agent[]> {
  const rows = await signedFetch<BackendAgent[]>("/api/v1/u/agents/stop-all", {
    method: "POST",
  })
  return rows.map(toClientAgent)
}

// ── Trades (WIRED via /hub/trades/{agent_id}) ──────────────────────────────

interface BackendIndexerRow {
  tx_hash: string
  user_id: string
  agent_id: string
  kind: string
  amount_usdt: string | null
  block_number: number
  tags: Record<string, unknown>
  created_at: string
}

interface BackendTradeRow {
  id: string
  agent_id: string
  side: string
  entry_price: number
  exit_price: number | null
  size_usdt: number
  leverage: number
  pnl: number | null
  strategy: string
  close_reason: string | null
  opened_at: string
  closed_at: string | null
}

const INDEXER_EPOCH = "1970-01-01T00:00:00Z"

function mapTradeRow(r: BackendTradeRow): Trade {
  return {
    id: r.id,
    agent_id: r.agent_id,
    side: (r.side as Trade["side"]) ?? "long",
    entry_price: r.entry_price,
    exit_price: r.exit_price,
    size_usdt: r.size_usdt,
    leverage: r.leverage,
    pnl: r.pnl,
    strategy: r.strategy,
    close_reason: (r.close_reason as Trade["close_reason"]) ?? null,
    opened_at: r.opened_at,
    closed_at: r.closed_at,
  }
}

export async function listTrades(agentId?: string): Promise<Trade[]> {
  if (agentId) {
    const body = await signedFetch<{ rows: BackendTradeRow[] }>(
      `/api/v1/u/hub/trades/${agentId}?limit=500`,
    )
    return body.rows.map(mapTradeRow)
  }
  // Merged view: indexer mirror is stub-only, so fan out per-agent trade calls
  // and concat. Failures per-agent are swallowed so one bad VM doesn't kill the
  // dashboard chart.
  try {
    const agents = await listAgents()
    const results = await Promise.all(
      agents.map(async (a) => {
        try {
          const body = await signedFetch<{ rows: BackendTradeRow[] }>(
            `/api/v1/u/hub/trades/${a.id}?limit=500`,
          )
          return body.rows.map(mapTradeRow)
        } catch {
          return [] as Trade[]
        }
      }),
    )
    return results.flat()
  } catch {
    return []
  }
}

// ── Strategies (WIRED) ─────────────────────────────────────────────────────

interface BackendStrategy {
  id: string
  name: string
  source: "builtin" | "marketplace" | "authored"
  code_blob?: string | null
  marketplace_id?: string | null
  created_at?: string
}

function toClientStrategy(b: BackendStrategy): Strategy {
  return {
    id: b.id,
    name: b.name,
    source: b.source,
    installed_at: b.created_at ?? new Date(0).toISOString(),
    param_schema: null,
  } as Strategy
}

export async function listStrategies(): Promise<{
  installed: Strategy[]
  authored: Strategy[]
}> {
  const rows = await signedFetch<BackendStrategy[]>("/api/v1/u/strategies")
  const mapped = rows.map(toClientStrategy)
  return {
    installed: mapped.filter((s) => s.source !== "authored"),
    authored: mapped.filter((s) => s.source === "authored"),
  }
}

// ── Secrets (WIRED — hub-local, not proxied) ───────────────────────────────

export async function listSecretKeys(): Promise<string[]> {
  const body = await signedFetch<{ keys: string[] }>("/api/v1/secrets")
  return body.keys
}

export async function setSecret(keyName: string, value: string): Promise<void> {
  await signedFetch("/api/v1/secrets", {
    method: "POST",
    body: { key_name: keyName, value },
  })
}

export async function deleteSecret(keyName: string): Promise<void> {
  await signedFetch(`/api/v1/secrets/${keyName}`, { method: "DELETE" })
}

// ── Indexer (WIRED — same /hub/indexer/since source as trades) ────────────

export async function listIndexer(filter: IndexerFilter): Promise<IndexerRow[]> {
  const fromTs = filter.from ?? INDEXER_EPOCH
  const body = await signedFetch<{ rows: BackendIndexerRow[] }>(
    `/api/v1/u/hub/indexer/since?ts=${encodeURIComponent(fromTs)}&limit=1000`,
  )
  let rows: IndexerRow[] = body.rows.map((r) => ({
    tx_hash: r.tx_hash,
    agent_id: r.agent_id,
    kind: r.kind as IndexerRow["kind"],
    amount_usdt: r.amount_usdt != null ? Number(r.amount_usdt) : null,
    block_number: r.block_number,
    tags: r.tags as IndexerRow["tags"],
    created_at: r.created_at,
  }))
  if (filter.kind) rows = rows.filter((r) => r.kind === filter.kind)
  if (filter.agent_id) rows = rows.filter((r) => r.agent_id.startsWith(filter.agent_id!))
  if (filter.min_amount != null)
    rows = rows.filter((r) => (r.amount_usdt ?? 0) >= filter.min_amount!)
  if (filter.to) rows = rows.filter((r) => r.created_at <= filter.to!)
  return rows
}

// ── Logs (WIRED — GET /hub/logs/{agent_id}) ───────────────────────────────

interface BackendLogRow {
  level: string
  message: string
  timestamp: string
}

export async function listLogs(agentId: string): Promise<LogEntry[]> {
  try {
    const body = await signedFetch<{ rows: BackendLogRow[] }>(`/api/v1/u/hub/logs/${agentId}`)
    return body.rows.map<LogEntry>((r) => ({
      level: r.level as LogEntry["level"],
      message: r.message,
      timestamp: r.timestamp,
    }))
  } catch (e: unknown) {
    // Endpoint not in deployed image yet — return empty instead of crashing.
    const status = (e as { status?: number })?.status
    if (status === 404) return []
    throw e
  }
}

// ── Credits (DEMO — hub/credits/ module is empty) ─────────────────────────

export async function getCredits(): Promise<Credits> {
  await latency()
  return { balance_ah: demoCreditBalance, last_debit_at: null }
}

export async function listLedger(): Promise<LedgerRow[]> {
  await latency()
  return demoLedger as unknown as LedgerRow[]
}

// ── Marketplace (DEMO — hub/marketplace/ module is empty) ─────────────────

export async function listMarketplace(
  sort: MarketplaceSort = "installs",
): Promise<MarketplaceItem[]> {
  await latency()
  const copy = [...demoMarketplace]
  if (sort === "installs") copy.sort((a, b) => b.installs - a.installs)
  if (sort === "reports") copy.sort((a, b) => b.reports - a.reports)
  if (sort === "recent") copy.sort((a, b) => b.created_at.localeCompare(a.created_at))
  return copy as unknown as MarketplaceItem[]
}

export async function getMarketplaceItem(id: string): Promise<MarketplaceItem | null> {
  await latency()
  return (demoMarketplace.find((m) => m.id === id) as unknown as MarketplaceItem | null) ?? null
}

// ── Sessions + API keys (DEMO) ────────────────────────────────────────────

export async function listSessions(): Promise<SessionKey[]> {
  await latency()
  return demoSessionKeys as unknown as SessionKey[]
}

export async function getApiKeyHint(): Promise<string | null> {
  await latency()
  return demoApiKeyHint
}

// Consumed for side-effect (suppress unused warning in callers that only
// import demoIndexer directly). Kept for backward-compat with older tests.
export const _demoIndexerFixture = demoIndexer
