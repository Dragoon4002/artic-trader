/**
 * User-scoped secret storage — plaintext over TLS, hub encrypts at rest.
 * Never returns plaintext or ciphertext; list returns key names only.
 *
 * @source hub/secrets/service.py
 */
import { z } from "zod"

// ── POST /api/v1/secrets ───────────────────────────────────────────────────

export const SecretWriteSchema = z.object({
  key_name: z.string(),
  value: z.string(), // plaintext; encrypted before persist
})
export type SecretWrite = z.infer<typeof SecretWriteSchema>

export const SecretPutResponseSchema = z.object({
  ok: z.boolean(),
  key_name: z.string(),
})
export type SecretPutResponse = z.infer<typeof SecretPutResponseSchema>

// ── GET /api/v1/secrets ────────────────────────────────────────────────────

export const SecretsListResponseSchema = z.object({
  keys: z.array(z.string()),
})
export type SecretsListResponse = z.infer<typeof SecretsListResponseSchema>

// ── DELETE /api/v1/secrets/{key_name} ──────────────────────────────────────

export const SecretDeleteResponseSchema = z.object({ ok: z.boolean() })
export type SecretDeleteResponse = z.infer<typeof SecretDeleteResponseSchema>
