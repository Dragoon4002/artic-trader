/**
 * Market data — live prices (Pyth) + cached candles (TwelveData).
 *
 * @source hub/market/router.py
 * @source hub/market/price_feed.py (price_cache shape)
 * @source hub/market/twelvedata.py (candle shape)
 */
import { z } from "zod"
import { Iso8601Schema } from "./shared"

// ── GET /api/market/price/{symbol} ─────────────────────────────────────────

export const PriceResponseSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  fetched_at: Iso8601Schema,
})
export type PriceResponse = z.infer<typeof PriceResponseSchema>

// ── GET /api/market/prices ─────────────────────────────────────────────────

export const PricesResponseSchema = z.record(z.string(), PriceResponseSchema)
export type PricesResponse = z.infer<typeof PricesResponseSchema>

// ── GET /api/market/candles ────────────────────────────────────────────────

export const CandleSchema = z.object({
  datetime: z.string(), // TwelveData returns "YYYY-MM-DD HH:MM:SS"
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number(),
})
export type Candle = z.infer<typeof CandleSchema>

export const CandlesResponseSchema = z.object({
  symbol: z.string(),
  interval: z.string(),
  candles: z.array(CandleSchema),
  cached: z.boolean(),
  stale: z.boolean().optional(),
  error: z.string().optional(),
})
export type CandlesResponse = z.infer<typeof CandlesResponseSchema>

// ── Query params (not a body, but typed for clients) ───────────────────────

export const CandlesQuerySchema = z.object({
  symbol: z.string(),
  interval: z.string().default("15m"),
})
export type CandlesQuery = z.infer<typeof CandlesQuerySchema>
