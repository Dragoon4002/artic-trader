"use client"

/**
 * Dev harness for step 1b of the auth runbook (docs/alpha/runtime-flow.md §8).
 *
 * Generates a one-shot Cosmos-style secp256k1 wallet + ephemeral session key,
 * fetches /auth/nonce, builds the ADR-36 SignDoc, signs it, and posts to
 * /auth/verify. Renders every step's request/response so you can inspect where
 * things break.
 *
 * Known caveat: hub rebuilds `issued_at` from `auth_nonce.created_at` (DB
 * insert timestamp), not the value we pass. If the DB stamp differs from our
 * client-side `new Date()` by more than zero ms, the signature is wrong and
 * /auth/verify returns 401. Fix options:
 *   (a) hub patch: return `issued_at` in NonceResponse; sign exactly that.
 *   (b) dev bypass: add /auth/dev-token guarded by ENV=dev.
 */

import { useCallback, useMemo, useState } from "react"
import { Check, Copy, Play, X as XIcon } from "lucide-react"
import { secp256k1 } from "@noble/curves/secp256k1.js"
import { sha256 } from "@noble/hashes/sha2.js"
import { ripemd160 } from "@noble/hashes/legacy.js"
import { bech32 } from "bech32"

type StepStatus = "pending" | "running" | "ok" | "error"
interface Step {
  id: string
  label: string
  status: StepStatus
  detail?: string
  duration_ms?: number
}

export default function AuthTestV1() {
  const [hubUrl, setHubUrl] = useState("http://localhost:9000")
  const [chain, setChain] = useState("initia-testnet")
  const [hrp, setHrp] = useState("init")
  const [running, setRunning] = useState(false)
  const [steps, setSteps] = useState<Step[]>([])
  const [result, setResult] = useState<null | {
    address: string
    nonce: string
    access_token: string
    session_id: string
    init_username: string | null
    session_priv_hex: string
  }>(null)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async () => {
    setRunning(true)
    setResult(null)
    setError(null)
    setSteps([])
    try {
      const out = await runAuthFlow({
        hubUrl: hubUrl.replace(/\/+$/, ""),
        chain,
        hrp,
        onStep: (s) =>
          setSteps((prev) => {
            const idx = prev.findIndex((p) => p.id === s.id)
            return idx === -1 ? [...prev, s] : prev.map((p, i) => (i === idx ? s : p))
          }),
      })
      setResult(out)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setRunning(false)
    }
  }, [hubUrl, chain, hrp])

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Auth flow v1 — dev harness</h1>
        <p className="mt-2 text-sm text-foreground/60">
          Generates a throwaway Cosmos wallet + session key, signs an ADR-36 message,
          and exchanges it for a hub JWT. Keys never leave this tab.
        </p>
      </header>

      <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Field label="Hub URL">
            <input
              className={inputCls}
              value={hubUrl}
              onChange={(e) => setHubUrl(e.target.value)}
            />
          </Field>
          <Field label="Chain">
            <input
              className={inputCls}
              value={chain}
              onChange={(e) => setChain(e.target.value)}
            />
          </Field>
          <Field label="Bech32 HRP">
            <input
              className={inputCls}
              value={hrp}
              onChange={(e) => setHrp(e.target.value)}
            />
          </Field>
        </div>
        <div className="mt-5 flex items-center gap-3">
          <button
            onClick={run}
            disabled={running}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--color-accent-warm,#E8A27A)] px-4 py-2 text-sm font-semibold text-black transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Play size={14} />
            {running ? "Running…" : "Run auth flow"}
          </button>
          <p className="text-[11px] text-foreground/50">
            Opens CORS requests to {hubUrl || "(unset)"}. Allowed origins are set in hub/server.py.
          </p>
        </div>
      </section>

      {steps.length > 0 && (
        <section className="mt-6 overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
          <ul className="divide-y divide-white/5">
            {steps.map((s) => (
              <StepRow key={s.id} step={s} />
            ))}
          </ul>
        </section>
      )}

      {error && (
        <section className="mt-6 rounded-xl border border-[var(--color-red)]/40 bg-[var(--color-red)]/10 p-4 text-sm text-[var(--color-red-light)]">
          <p className="font-semibold">Run failed</p>
          <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-xs">{error}</pre>
        </section>
      )}

      {result && (
        <section className="mt-6 space-y-3 rounded-xl border border-[var(--color-teal)]/30 bg-[var(--color-teal)]/[0.05] p-5">
          <h2 className="text-sm font-semibold text-[var(--color-teal)]">
            Got JWT + session_id
          </h2>
          <KV label="wallet address" value={result.address} />
          <KV label="nonce" value={result.nonce} />
          <KV label="access_token" value={result.access_token} wide />
          <KV label="session_id" value={result.session_id} />
          <KV label="session private key (hex)" value={result.session_priv_hex} wide />
          <KV label="init_username" value={result.init_username ?? "(none)"} />
          <p className="mt-3 text-[11px] text-foreground/50">
            Paste <code className="rounded bg-white/[0.04] px-1">access_token</code> into Postman as{" "}
            <code className="rounded bg-white/[0.04] px-1">Authorization: Bearer &lt;token&gt;</code>.
          </p>
        </section>
      )}
    </main>
  )
}

// ── Steps UI ────────────────────────────────────────────────────────────────

function StepRow({ step }: { step: Step }) {
  const tone =
    step.status === "ok"
      ? "text-[var(--color-teal)]"
      : step.status === "error"
        ? "text-[var(--color-red-light)]"
        : step.status === "running"
          ? "text-[var(--color-accent-warm,#E8A27A)]"
          : "text-foreground/40"
  const icon =
    step.status === "ok" ? (
      <Check size={13} />
    ) : step.status === "error" ? (
      <XIcon size={13} />
    ) : (
      <span className={`h-2 w-2 rounded-full ${step.status === "running" ? "animate-pulse bg-current" : "bg-current/40"}`} />
    )
  return (
    <li className="flex items-start gap-3 p-4 text-sm">
      <span className={`mt-0.5 shrink-0 ${tone}`}>{icon}</span>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-2">
          <span className="font-medium text-foreground/80">{step.label}</span>
          {step.duration_ms != null && (
            <span className="font-mono text-[11px] text-foreground/40">
              {step.duration_ms}ms
            </span>
          )}
        </p>
        {step.detail && (
          <pre className="mt-1.5 max-h-56 overflow-auto rounded bg-black/40 p-3 font-mono text-[11px] leading-relaxed text-foreground/70">
            {step.detail}
          </pre>
        )}
      </div>
    </li>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-foreground/55">
        {label}
      </span>
      {children}
    </label>
  )
}

function KV({ label, value, wide }: { label: string; value: string; wide?: boolean }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-foreground/50">{label}</p>
      <div className={`mt-1 flex items-start gap-2 ${wide ? "flex-col md:flex-row" : ""}`}>
        <code className="flex-1 min-w-0 truncate rounded bg-black/40 px-2 py-1 font-mono text-xs text-foreground/80">
          {value}
        </code>
        <button
          onClick={copy}
          className="inline-flex items-center gap-1 rounded border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-foreground/70 hover:text-foreground"
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  )
}

const inputCls =
  "w-full rounded-md border border-white/10 bg-white/[0.02] px-3 py-2 text-sm font-mono text-foreground placeholder:text-foreground/30 focus:border-[var(--color-accent-warm,#E8A27A)] focus:outline-none"

// ── Auth flow implementation ────────────────────────────────────────────────

interface RunOpts {
  hubUrl: string
  chain: string
  hrp: string
  onStep: (s: Step) => void
}

async function runAuthFlow(opts: RunOpts) {
  const { hubUrl, chain, hrp, onStep } = opts

  // 1. Wallet keypair
  const t1 = performance.now()
  onStep({ id: "keys", label: "Generate wallet + session keypairs", status: "running" })
  const walletPriv = secp256k1.utils.randomSecretKey()
  const walletPub = secp256k1.getPublicKey(walletPriv, true) // 33-byte compressed
  const address = pubkeyToBech32(walletPub, hrp)
  const pubkey_b64 = b64encode(walletPub)

  const sessionPriv = secp256k1.utils.randomSecretKey()
  const sessionPub = secp256k1.getPublicKey(sessionPriv, true)
  const session_pub_b64 = b64encode(sessionPub)
  onStep({
    id: "keys",
    label: "Generate wallet + session keypairs",
    status: "ok",
    duration_ms: Math.round(performance.now() - t1),
    detail:
      `address       ${address}\n` +
      `wallet pub    ${pubkey_b64}\n` +
      `session pub   ${session_pub_b64}`,
  })

  // 2. POST /auth/nonce
  const t2 = performance.now()
  onStep({ id: "nonce", label: "POST /auth/nonce", status: "running" })
  const nonceRes = await fetch(`${hubUrl}/auth/nonce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ address, chain }),
  })
  const nonceBody = await safeJson(nonceRes)
  if (!nonceRes.ok) {
    onStep({
      id: "nonce",
      label: "POST /auth/nonce",
      status: "error",
      duration_ms: Math.round(performance.now() - t2),
      detail: `HTTP ${nonceRes.status}\n${JSON.stringify(nonceBody, null, 2)}`,
    })
    throw new Error(`nonce: ${nonceRes.status} ${JSON.stringify(nonceBody)}`)
  }
  const nonce = String(nonceBody.nonce ?? "")
  const issued_at_iso = String(nonceBody.issued_at ?? "")
  if (!issued_at_iso) {
    throw new Error(
      "nonce response missing `issued_at` — rebuild the hub image with the patched router"
    )
  }
  onStep({
    id: "nonce",
    label: "POST /auth/nonce",
    status: "ok",
    duration_ms: Math.round(performance.now() - t2),
    detail: JSON.stringify(nonceBody, null, 2),
  })

  // 3. Build canonical sign-in message. `issued_at` is the hub's DB-stamped
  // string echoed back in the nonce response — must be used verbatim.
  // `session_expires_at` is our choice, sent verbatim to /auth/verify.
  const session_expires_at_iso = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString()
  const message = buildSigninMessage({
    chain,
    address,
    nonce,
    session_pub: session_pub_b64,
    session_scope: "authenticated-actions",
    issued_at_iso,
    session_expires_at_iso,
  })
  onStep({
    id: "message",
    label: "Build canonical sign-in message (client-side)",
    status: "ok",
    detail: message,
  })

  // 4. ADR-36 sign
  const t4 = performance.now()
  onStep({ id: "sign", label: "ADR-36 sign message", status: "running" })
  const signDoc = buildAdr36SignDoc(address, message)
  const digest = sha256(signDoc)
  const compactSig = secp256k1.sign(digest, walletPriv)
  const signature_b64 = b64encode(compactSig)
  onStep({
    id: "sign",
    label: "ADR-36 sign message",
    status: "ok",
    duration_ms: Math.round(performance.now() - t4),
    detail: `sign-doc bytes: ${signDoc.length}\nsha256(doc):    ${hex(digest)}\nsignature b64:  ${signature_b64}`,
  })

  // 5. POST /auth/verify
  const t5 = performance.now()
  onStep({ id: "verify", label: "POST /auth/verify", status: "running" })
  const verifyReq = {
    address,
    chain,
    nonce,
    signature: signature_b64,
    pubkey: pubkey_b64,
    session_pub: session_pub_b64,
    session_scope: "authenticated-actions",
    session_expires_at: session_expires_at_iso,
  }
  const verifyRes = await fetch(`${hubUrl}/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(verifyReq),
  })
  const verifyBody = await safeJson(verifyRes)
  if (!verifyRes.ok) {
    onStep({
      id: "verify",
      label: "POST /auth/verify",
      status: "error",
      duration_ms: Math.round(performance.now() - t5),
      detail:
        `HTTP ${verifyRes.status}\n${JSON.stringify(verifyBody, null, 2)}\n\n` +
        `request:\n${JSON.stringify(verifyReq, null, 2)}`,
    })
    throw new Error(
      verifyRes.status === 401
        ? "verify: 401 — signature mismatch. Most likely `issued_at` drift vs hub's DB-stamped nonce.created_at. See file comments for fix."
        : `verify: ${verifyRes.status} ${JSON.stringify(verifyBody)}`
    )
  }
  onStep({
    id: "verify",
    label: "POST /auth/verify",
    status: "ok",
    duration_ms: Math.round(performance.now() - t5),
    detail: JSON.stringify(verifyBody, null, 2),
  })

  return {
    address,
    nonce,
    access_token: verifyBody.access_token as string,
    session_id: verifyBody.session_id as string,
    init_username: (verifyBody.init_username ?? null) as string | null,
    session_priv_hex: hex(sessionPriv),
  }
}

// ── Crypto + encoding helpers ───────────────────────────────────────────────

function pubkeyToBech32(pub: Uint8Array, hrp: string): string {
  const sha = sha256(pub)
  const rip = ripemd160(sha)
  const words = bech32.toWords(rip)
  return bech32.encode(hrp, words)
}

function buildSigninMessage(args: {
  chain: string
  address: string
  nonce: string
  session_pub: string
  session_scope: string
  issued_at_iso: string
  session_expires_at_iso: string
}) {
  return (
    `artic.trade wants you to sign in with your ${args.chain} account:\n` +
    `${args.address}\n` +
    `\n` +
    `Session public key: ${args.session_pub}\n` +
    `Scope: ${args.session_scope}\n` +
    `Nonce: ${args.nonce}\n` +
    `Issued At: ${args.issued_at_iso}\n` +
    `Expires At: ${args.session_expires_at_iso}`
  )
}

/** Amino JSON SignDoc for ADR-36 signArbitrary. Must be deterministic. */
function buildAdr36SignDoc(address: string, message: string): Uint8Array {
  const msgB64 = b64encode(new TextEncoder().encode(message))
  const doc = {
    account_number: "0",
    chain_id: "",
    fee: { amount: [], gas: "0" },
    memo: "",
    msgs: [
      {
        type: "sign/MsgSignData",
        value: { data: msgB64, signer: address },
      },
    ],
    sequence: "0",
  }
  // JSON.stringify preserves insertion order; the keys above are sorted
  // alphabetically top-down so output matches Python `json.dumps(..., sort_keys=True)`.
  return new TextEncoder().encode(JSON.stringify(doc))
}

function b64encode(bytes: Uint8Array): string {
  let s = ""
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s)
}

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

async function safeJson(r: Response): Promise<Record<string, unknown>> {
  const text = await r.text()
  try {
    return JSON.parse(text)
  } catch {
    return { _raw: text }
  }
}
