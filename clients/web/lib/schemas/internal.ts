/**
 * Internal push APIs. Web clients NEVER call these — included so the types
 * document is complete and shared helpers (e.g. mock servers, internal tools)
 * can compile against the same shapes.
 *
 * Auth headers (enforced by hub):
 *   - X-UserServer-Token  → user-server → hub callbacks (/internal/v1/*)
 *   - X-Hub-Secret        → admin image fetch (/internal/v1/images/*)
 *   - X-Internal-Secret   → agent → user-server pushes (future)
 *
 * @source hub/internal/router.py
 * @source hub/internal/images.py
 * @source docs/alpha/api-contracts.md §Internal
 */
import { z } from "zod"

// ── User-server → hub (all Phase-4 stubs today) ────────────────────────────

export const InternalNoopResponseSchema = z.object({
  ok: z.boolean(),
  noop: z.string().optional(),
})
export type InternalNoopResponse = z.infer<typeof InternalNoopResponseSchema>

// POST /internal/v1/credits/heartbeat
export const CreditsHeartbeatRequestSchema = z.object({
  alive_agents: z.number().int().nonnegative().optional(),
})
export type CreditsHeartbeatRequest = z.infer<typeof CreditsHeartbeatRequestSchema>

// POST /internal/v1/indexer/flush
export const IndexerFlushRequestSchema = z.object({
  rows: z.array(z.record(z.string(), z.unknown())).optional(),
})
export type IndexerFlushRequest = z.infer<typeof IndexerFlushRequestSchema>

// POST /internal/v1/otel/spans
export const OtelSpansRequestSchema = z.object({
  spans: z.array(z.record(z.string(), z.unknown())).optional(),
})
export type OtelSpansRequest = z.infer<typeof OtelSpansRequestSchema>

// ── Admin image fetch (X-Hub-Secret) ───────────────────────────────────────

export const ImageListItemSchema = z.object({
  name: z.string(),
  size: z.number().int().nonnegative(),
})
export type ImageListItem = z.infer<typeof ImageListItemSchema>

export const ImageListResponseSchema = z.object({
  available: z.array(ImageListItemSchema),
  expected: z.array(z.string()),
})
export type ImageListResponse = z.infer<typeof ImageListResponseSchema>

// GET /internal/v1/images/{name}  →  application/gzip tarball (not JSON)

// ── Agent → user-server pushes (documented for ref; user-server owns) ─────
// POST /agents/{id}/status          — every tick
// POST /trades                      — on open/close
// POST /logs                        — every 10 ticks (batched)
// POST /supervisor                  — supervisor decision events
// POST /signal-request              — LLM proxy dispatch
//
// Shapes live with the user-server once that service lands. Intentionally
// not typed here to avoid drift — see docs/alpha/api-contracts.md.
