/**
 * WebSocket streams. All messages follow `{type, data}` envelope.
 *
 * @source hub/ws/broadcaster.py (endpoints)
 * @source hub/ws/manager.py (broadcast payloads)
 * @source hub/proxy/ws.py (/ws/u/* proxy stub — returns 1011 until user-server lands)
 */
import { z } from "zod"
import { PriceResponseSchema } from "./market"

// ── Envelope ───────────────────────────────────────────────────────────────

export const WsEnvelopeSchema = z.object({
  type: z.string(),
  data: z.unknown(),
})
export type WsEnvelope = z.infer<typeof WsEnvelopeSchema>

// ── /ws/prices ─────────────────────────────────────────────────────────────

export const WsPricesMessageSchema = z.object({
  type: z.literal("prices"),
  data: z.record(z.string(), PriceResponseSchema),
})
export type WsPricesMessage = z.infer<typeof WsPricesMessageSchema>

// ── /ws/agents/{id}/status (container-internal today) ──────────────────────
// ── /ws/u/agents/{id}/status (client-facing — alpha; 1011 stub today) ──────

export const WsAgentStatusMessageSchema = z.object({
  type: z.literal("status"),
  data: z.record(z.string(), z.unknown()), // last-known registry snapshot
})
export type WsAgentStatusMessage = z.infer<typeof WsAgentStatusMessageSchema>

// ── /ws/agents/{id}/logs (+ /ws/u/* proxy) ─────────────────────────────────

export const WsAgentLogsMessageSchema = z.object({
  type: z.literal("logs"),
  data: z.array(z.record(z.string(), z.unknown())),
})
export type WsAgentLogsMessage = z.infer<typeof WsAgentLogsMessageSchema>

// ── Discriminated union of known messages ──────────────────────────────────

export const WsMessageSchema = z.union([
  WsPricesMessageSchema,
  WsAgentStatusMessageSchema,
  WsAgentLogsMessageSchema,
])
export type WsMessage = z.infer<typeof WsMessageSchema>
