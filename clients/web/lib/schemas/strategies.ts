/**
 * Strategy catalog — installed + authored. Served via hub's `/u/strategies`
 * proxy to the user-server.
 *
 * @source docs/alpha/api-contracts.md §User-scoped proxy
 */
import { z } from "zod"
import { Iso8601Schema, UuidSchema } from "./shared"

export const StrategySourceSchema = z.enum([
  "builtin",
  "marketplace",
  "authored",
])
export type StrategySourceT = z.infer<typeof StrategySourceSchema>

// ── GET /u/strategies — list item ──────────────────────────────────────────

export const StrategySchema = z.object({
  id: UuidSchema,
  name: z.string(),
  source: StrategySourceSchema,
  description: z.string(),
  installs: z.number().optional(),
  author: z.string().optional(),
  /** Wallet address (init1…) of the original creator. */
  creator_wallet: z.string().optional(),
  /** How many active agents currently use this strategy. */
  uses: z.number().optional(),
  /** 0–1 win rate across closed trades attributed to this strategy. */
  success_rate: z.number().optional(),
  updated_at: Iso8601Schema.optional(),
})
export type Strategy = z.infer<typeof StrategySchema>

export const StrategyListResponseSchema = z.object({
  installed: z.array(StrategySchema),
  authored: z.array(StrategySchema),
})
export type StrategyListResponse = z.infer<typeof StrategyListResponseSchema>

// ── POST /u/strategies — upload ────────────────────────────────────────────

export const CreateStrategyRequestSchema = z.object({
  name: z.string().min(1),
  description: z.string(),
  code: z.string(), // sandboxed Python source
})
export type CreateStrategyRequest = z.infer<typeof CreateStrategyRequestSchema>

// ── DELETE /u/strategies/{id} ──────────────────────────────────────────────

export const DeleteStrategyResponseSchema = z.object({ ok: z.boolean() })
export type DeleteStrategyResponse = z.infer<typeof DeleteStrategyResponseSchema>
