/**
 * Thin fetch wrapper. Loads JWT from localStorage (populated by useHubAuth),
 * sets Authorization, and retries twice on 202 VM_WAKING (cold wake).
 */

import { loadJwt } from "./hub-auth"

const HUB_URL =
  (process.env.NEXT_PUBLIC_HUB_URL as string | undefined) || "http://localhost:9000"

export class HubError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public body?: unknown,
  ) {
    super(message)
  }
}

export interface SignedFetchOpts extends Omit<RequestInit, "body"> {
  body?: unknown
  /** Max retries on 202 VM_WAKING. Default 4 × 3s = 12s budget. */
  wakeRetries?: number
}

export async function signedFetch<T = unknown>(
  path: string,
  opts: SignedFetchOpts = {},
): Promise<T> {
  const jwt = loadJwt()
  const url = path.startsWith("http") ? path : `${HUB_URL}${path}`
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((opts.headers as Record<string, string>) ?? {}),
  }
  if (jwt?.access_token) {
    headers.Authorization = `Bearer ${jwt.access_token}`
  }
  const body = opts.body != null ? JSON.stringify(opts.body) : undefined
  const wakeRetries = opts.wakeRetries ?? 4

  for (let attempt = 0; attempt <= wakeRetries; attempt++) {
    const res = await fetch(url, {
      ...opts,
      headers,
      body,
      credentials: "include",
    })

    // 204 No Content
    if (res.status === 204) return undefined as T

    let parsed: unknown = null
    const text = await res.text()
    if (text) {
      try {
        parsed = JSON.parse(text)
      } catch {
        parsed = text
      }
    }

    if (res.ok) return parsed as T

    // Hub returns {error:{code,message}} for wake-proxy paths.
    const err = (parsed as { error?: { code?: string; message?: string } })?.error
    const code = err?.code ?? `HTTP_${res.status}`
    const message = err?.message ?? res.statusText

    if (res.status === 202 && code === "VM_WAKING" && attempt < wakeRetries) {
      const retryAfter = parseInt(res.headers.get("Retry-After") ?? "3", 10)
      await new Promise((r) => setTimeout(r, retryAfter * 1000))
      continue
    }

    throw new HubError(res.status, code, message, parsed)
  }

  throw new HubError(202, "VM_WAKING", "VM did not wake in time")
}
