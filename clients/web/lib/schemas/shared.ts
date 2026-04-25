/**
 * Shared primitives + enums reused across every hub-facing payload.
 *
 * Enum values match the richer web-side taxonomy. Hub will shift to these as
 * user-server ships — web remains the superset.
 */
import { z } from "zod"

// ── Scalars ────────────────────────────────────────────────────────────────

export const Iso8601Schema = z.string() // ISO-8601 timestamp string (hub returns .isoformat())
export type Iso8601 = z.infer<typeof Iso8601Schema>

export const UuidSchema = z.string() // server-assigned; client treats as opaque
export type Uuid = z.infer<typeof UuidSchema>

// ── Agent lifecycle ────────────────────────────────────────────────────────

export const AgentStatusSchema = z.enum([
  "alive",
  "stopped",
  "starting",
  "error",
  "halted",
])
export type AgentStatusT = z.infer<typeof AgentStatusSchema>

export const SideSchema = z.enum(["long", "short", "flat"])
export type SideT = z.infer<typeof SideSchema>

export const CloseReasonSchema = z.enum(["TP", "SL", "SUPERVISOR", "MANUAL"])
export type CloseReasonT = z.infer<typeof CloseReasonSchema>

export const LogLevelSchema = z.enum([
  "init",
  "llm",
  "tick",
  "action",
  "sl_tp",
  "supervisor",
  "warn",
  "error",
  // Legacy stdlib-style levels emitted by older agent images (artic-agent:v0
  // applies _LEVEL_MAP before push). Kept so existing VMs keep streaming.
  "debug",
  "info",
])
export type LogLevelT = z.infer<typeof LogLevelSchema>
