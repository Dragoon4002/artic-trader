/**
 * Liveness + readiness probes.
 *
 * @source hub/server.py
 */
import { z } from "zod"

// ── GET /health ────────────────────────────────────────────────────────────

export const HealthResponseSchema = z.object({
  ok: z.boolean(),
  service: z.string(),
})
export type HealthResponse = z.infer<typeof HealthResponseSchema>

// ── GET /health/ready ──────────────────────────────────────────────────────

export const ReadyResponseSchema = z.object({
  ok: z.boolean(),
  checks: z.record(z.string(), z.string()), // e.g. { db: "ok" }
})
export type ReadyResponse = z.infer<typeof ReadyResponseSchema>
