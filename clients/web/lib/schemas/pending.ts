/**
 * @pending — endpoints the hub does NOT yet serve. Shapes drafted from
 * `docs/alpha/api-contracts.md` so the demo dashboard can compile, but the
 * contract is not stable until the corresponding hub / user-server modules
 * land. Do not rely on these in new code paths — read from `lib/demo-data`
 * via typed `lib/api.ts` fetchers, which are explicitly cast.
 *
 * When each endpoint lands, move its schema into the matching canonical
 * module (agents.ts, etc.) and delete from here.
 */
import { z } from "zod"
import { Iso8601Schema, UuidSchema } from "./shared"

// ── Credits — /api/v1/credits, /api/v1/credits/ledger ──────────────────────

export const CreditsSchema = z.object({
  balance_ah: z.number(),
  last_debit_at: Iso8601Schema.nullable().optional(),
})
export type Credits = z.infer<typeof CreditsSchema>

export const LedgerRowSchema = z.object({
  id: UuidSchema,
  delta: z.number(),
  reason: z.enum(["tick_debit", "admin_grant", "halt_refund"]),
  agent_id: UuidSchema.optional(),
  created_at: Iso8601Schema,
})
export type LedgerRow = z.infer<typeof LedgerRowSchema>

// ── Indexer — /api/v1/indexer/tx ───────────────────────────────────────────

export const IndexerRowSchema = z.object({
  tx_hash: z.string(),
  agent_id: UuidSchema,
  kind: z.enum(["trades", "supervise"]),
  amount_usdt: z.number().nullable(),
  symbol: z.string(),
  side: z.enum(["long", "short"]).optional(),
  block: z.number(),
  created_at: Iso8601Schema,
})
export type IndexerRow = z.infer<typeof IndexerRowSchema>

export const IndexerFilterSchema = z.object({
  scope: z.enum(["mine", "all"]).default("mine"),
  agent_id: z.string().optional(),
  kind: z.enum(["trades", "supervise"]).optional(),
  min_amount: z.number().nonnegative().optional(),
  from: Iso8601Schema.optional(),
  to: Iso8601Schema.optional(),
})
export type IndexerFilter = z.infer<typeof IndexerFilterSchema>

// ── Marketplace — /api/v1/marketplace ──────────────────────────────────────

export const MarketplaceItemSchema = z.object({
  id: UuidSchema,
  name: z.string(),
  description: z.string(),
  author: z.string(),
  installs: z.number(),
  reports: z.number(),
  created_at: Iso8601Schema,
  code_preview: z.string(),
})
export type MarketplaceItem = z.infer<typeof MarketplaceItemSchema>

export const MarketplaceSortSchema = z.enum(["installs", "recent", "reports"])
export type MarketplaceSort = z.infer<typeof MarketplaceSortSchema>

export const MarketplaceReportRequestSchema = z.object({
  reason: z.string().min(1),
})
export type MarketplaceReportRequest = z.infer<typeof MarketplaceReportRequestSchema>
