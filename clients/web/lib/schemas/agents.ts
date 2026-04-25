/**
 * Agent lifecycle + trade + log payloads.
 *
 * Served through hub's `/api/v1/u/*` proxy which forwards to the caller's
 * user-server. From the client's POV the hub is the contract boundary, so the
 * payload shapes are pinned here even though the user-server owns the data.
 *
 * @source docs/alpha/api-contracts.md §User-scoped proxy
 */
import { z } from "zod"
import {
  AgentStatusSchema,
  CloseReasonSchema,
  Iso8601Schema,
  LogLevelSchema,
  SideSchema,
  UuidSchema,
} from "./shared"

// ── Agent (detail + list row) ──────────────────────────────────────────────

export const AgentSchema = z.object({
  id: UuidSchema,
  name: z.string(),
  symbol: z.string(),
  status: AgentStatusSchema,
  price: z.number(),
  side: SideSchema,
  amount_usdt: z.number(),
  leverage: z.number(),
  unrealised_pnl: z.number().nullable(),
  strategy: z.string(),
  llm_provider: z.string(),
  llm_model: z.string(),
  poll_seconds: z.number(),
  supervisor_interval: z.number(),
  tp_pct: z.number().nullable(),
  sl_pct: z.number().nullable(),
  created_at: Iso8601Schema,
})
export type Agent = z.infer<typeof AgentSchema>

// ── POST /u/agents — create ────────────────────────────────────────────────

export const CreateAgentRequestSchema = z.object({
  name: z.string().min(1),
  symbol: z.string().min(1),
  amount_usdt: z.number().positive(),
  leverage: z.number().positive(),
  strategy: z.string(),
  llm_provider: z.string(),
  llm_model: z.string(),
  poll_seconds: z.number().positive(),
  supervisor_interval: z.number().positive(),
  tp_pct: z.number().nullable().optional(),
  sl_pct: z.number().nullable().optional(),
})
export type CreateAgentRequest = z.infer<typeof CreateAgentRequestSchema>

// ── PATCH /u/agents/{id} — update ──────────────────────────────────────────

export const UpdateAgentRequestSchema = CreateAgentRequestSchema.partial()
export type UpdateAgentRequest = z.infer<typeof UpdateAgentRequestSchema>

// ── POST /u/agents/{id}/start | /stop | /u/agents/start-all | /stop-all ────

export const AgentLifecycleResponseSchema = z.object({
  ok: z.boolean(),
  status: AgentStatusSchema.optional(),
})
export type AgentLifecycleResponse = z.infer<typeof AgentLifecycleResponseSchema>

// ── Trade ──────────────────────────────────────────────────────────────────

export const TradeSchema = z.object({
  id: UuidSchema,
  agent_id: UuidSchema,
  side: z.enum(["long", "short"]),
  entry_price: z.number(),
  exit_price: z.number().nullable(),
  size_usdt: z.number(),
  leverage: z.number(),
  pnl: z.number().nullable(),
  strategy: z.string(),
  close_reason: CloseReasonSchema.nullable(),
  opened_at: Iso8601Schema,
  closed_at: Iso8601Schema.nullable(),
  tx_hash: z.string().nullable().optional(),
})
export type Trade = z.infer<typeof TradeSchema>

// ── Log entry ──────────────────────────────────────────────────────────────

export const LogEntrySchema = z.object({
  level: LogLevelSchema,
  message: z.string(),
  timestamp: Iso8601Schema,
})
export type LogEntry = z.infer<typeof LogEntrySchema>
