/**
 * Canonical hub-contract types for the web client.
 *
 * Split by domain; this file is the single import surface:
 *
 *   import { AgentSchema, Agent, ErrorResponse } from "@/lib/schemas"
 *
 * See `docs/connections/api-contracts.md` for the human-readable contract
 * index + endpoint-to-type map. Every schema carries an `@source` pointer to
 * the hub file that defines the wire shape.
 *
 * Pending endpoints (credits, ledger, indexer, marketplace) live in
 * `./pending` and are re-exported for back-compat with demo-data pages; do
 * not rely on their shapes in new code until they're promoted.
 */

export * from "./shared"
export * from "./errors"
export * from "./auth"
export * from "./agents"
export * from "./strategies"
export * from "./market"
export * from "./secrets"
export * from "./health"
export * from "./ws"
export * from "./internal"

// Demo-only / not-yet-served. Promote a file out of pending.ts when its
// backing endpoint ships.
export * from "./pending"
