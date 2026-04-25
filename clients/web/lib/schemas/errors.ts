/**
 * Error envelope returned by every hub route on non-2xx status.
 *
 * @source hub/utils/errors.py (install_error_handlers + HubError)
 * @source docs/alpha/api-contracts.md §Error shape
 */
import { z } from "zod"

// Codes emitted by hub/utils/errors.py _code_for_status plus custom HubError
// codes listed in the alpha contract. Keep as soft string (z.string()) + known
// union so unknown codes from future branches don't throw on parse.
export const KnownErrorCode = [
  // mapped from HTTP status (hub/utils/errors.py)
  "BAD_REQUEST",
  "UNAUTHENTICATED",
  "FORBIDDEN",
  "NOT_FOUND",
  "CONFLICT",
  "VALIDATION_ERROR",
  "RATE_LIMITED",
  "INTERNAL_ERROR",
  "UPSTREAM_ERROR",
  "UNAVAILABLE",
  "ERROR",
  // alpha-spec custom codes (docs/alpha/api-contracts.md)
  "AUTH_REQUIRED",
  "AUTH_INVALID",
  "CREDITS_DEPLETED",
  "VM_WAKING",
  "VM_UNAVAILABLE",
] as const

export const ErrorCodeSchema = z.string()
export type ErrorCodeT = (typeof KnownErrorCode)[number] | (string & {})

export const ErrorBodySchema = z.object({
  code: ErrorCodeSchema,
  message: z.string(),
  request_id: z.string().optional().default(""),
  details: z.record(z.string(), z.unknown()).optional(),
})
export type ErrorBody = z.infer<typeof ErrorBodySchema>

export const ErrorResponseSchema = z.object({
  error: ErrorBodySchema,
})
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>
