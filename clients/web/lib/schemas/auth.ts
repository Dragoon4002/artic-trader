/**
 * Wallet-signature auth flow + session-key management + API-key issuance.
 *
 * @source hub/auth/router.py
 * @source docs/alpha/api-contracts.md §Auth
 */
import { z } from "zod"
import { Iso8601Schema, UuidSchema } from "./shared"

// ── POST /auth/nonce ───────────────────────────────────────────────────────

export const NonceRequestSchema = z.object({
  address: z.string().min(1),
  chain: z.string().min(1),
})
export type NonceRequest = z.infer<typeof NonceRequestSchema>

export const NonceResponseSchema = z.object({
  nonce: z.string(),
  message: z.string(), // preview of canonical sign-in message
  expires_at: Iso8601Schema,
})
export type NonceResponse = z.infer<typeof NonceResponseSchema>

// ── POST /auth/verify ──────────────────────────────────────────────────────

export const VerifyRequestSchema = z.object({
  address: z.string(),
  chain: z.string(),
  nonce: z.string(),
  signature: z.string(),
  pubkey: z.string(),
  session_pub: z.string(),
  session_scope: z.string().default("authenticated-actions"),
  session_expires_at: Iso8601Schema,
})
export type VerifyRequest = z.infer<typeof VerifyRequestSchema>

export const VerifyResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("bearer"),
  session_id: z.string(),
  init_username: z.string().nullable().optional(),
})
export type VerifyResponse = z.infer<typeof VerifyResponseSchema>

// ── POST /auth/refresh ─────────────────────────────────────────────────────

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("bearer"),
})
export type TokenResponse = z.infer<typeof TokenResponseSchema>

// ── GET /auth/me ───────────────────────────────────────────────────────────

export const MeResponseSchema = z.object({
  id: UuidSchema,
  wallet_address: z.string(),
  wallet_chain: z.string(),
  init_username: z.string().nullable(),
})
export type MeResponse = z.infer<typeof MeResponseSchema>
export type Me = MeResponse // legacy alias

// ── GET /auth/session ──────────────────────────────────────────────────────

export const SessionInfoSchema = z.object({
  session_id: z.string(),
  scope: z.string(),
  expires_at: Iso8601Schema,
  revoked_at: Iso8601Schema.nullable(),
  created_at: Iso8601Schema.nullable(),
})
export type SessionInfo = z.infer<typeof SessionInfoSchema>

// Web-side extension — not returned by /auth/session today but used by demo
// settings page. Hub will align when user-server owns session listing.
export const SessionKeySchema = SessionInfoSchema.extend({
  last_used_at: Iso8601Schema.optional(),
  ua_hint: z.string().optional(),
})
export type SessionKey = z.infer<typeof SessionKeySchema>

// ── DELETE /auth/session ───────────────────────────────────────────────────

export const RevokeSessionResponseSchema = z.object({ revoked: z.boolean() })
export type RevokeSessionResponse = z.infer<typeof RevokeSessionResponseSchema>

// ── POST /api/keys ─────────────────────────────────────────────────────────

export const ApiKeyResponseSchema = z.object({
  api_key: z.string(), // one-time plaintext reveal
})
export type ApiKeyResponse = z.infer<typeof ApiKeyResponseSchema>

// ── Session-key request headers (state-changing calls) ─────────────────────
//
// Not a body type — these HTTP headers must accompany every POST/PATCH/DELETE
// signed by the delegated session key. See docs/alpha/api-contracts.md.

export const SessionKeyHeaders = {
  sessionId: "X-Session-Id",
  sessionNonce: "X-Session-Nonce", // monotonic integer
  sessionSig: "X-Session-Sig", // base64 sig over canonical request
} as const
