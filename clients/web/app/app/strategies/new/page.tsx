"use client"

import dynamic from "next/dynamic"
import Link from "next/link"
import { useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  Info,
  Save,
  ShieldAlert,
  Upload,
  X,
} from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import {
  ALLOWED_BUILTINS,
  ALLOWED_IMPORTS,
  CPU_BUDGET_MS,
  FORBIDDEN_MODULES,
  FORBIDDEN_NAMES,
  LintIssue,
  MEMORY_BUDGET_MB,
  REQUIRED_FN,
  SIGNATURE,
  STARTER_CODE,
  lintStrategy,
} from "@/lib/strategy-sandbox"

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[520px] items-center justify-center rounded-md border border-white/10 bg-black/40 text-sm text-foreground/40">
      Loading editor…
    </div>
  ),
})

export default function NewStrategyPage() {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [code, setCode] = useState(STARTER_CODE)
  const [publish, setPublish] = useState(false)

  const issues = useMemo(() => lintStrategy(code), [code])
  const errCount = issues.filter((i) => i.severity === "error").length
  const warnCount = issues.filter((i) => i.severity === "warn").length
  const canSave = name.trim().length > 0 && errCount === 0

  const payload = {
    source: "authored",
    name: name.trim(),
    description: description.trim(),
    code_blob: code,
    publish_to_marketplace: publish,
  }

  return (
    <div className="space-y-8">
      <Link
        href="/app/strategies"
        className="inline-flex items-center gap-1.5 text-xs text-foreground/50 hover:text-foreground"
      >
        <ArrowLeft size={12} /> Back to strategies
      </Link>

      <PageHeader
        title="New strategy"
        subtitle={
          <>
            Save sends a signed <code className="font-mono">POST /u/strategies</code>. Code runs
            under RestrictedPython inside your user-server at tick time.
          </>
        }
        action={
          <div className="flex items-center gap-2">
            <Link
              href="/app/strategies"
              className="rounded-md border border-white/10 bg-white/[0.02] px-4 py-2 text-sm font-semibold text-foreground/70 transition hover:text-foreground"
            >
              Cancel
            </Link>
            <button
              disabled
              title={
                !canSave
                  ? errCount > 0
                    ? `${errCount} lint error${errCount > 1 ? "s" : ""} — fix before save`
                    : "Name required"
                  : "Hub auth wiring pending"
              }
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] opacity-50"
            >
              <Save size={14} />
              Save{publish ? " + publish" : ""}
            </button>
          </div>
        }
      />

      <PendingHub what="POST /u/strategies proxied to user-server; publish_to_marketplace triggers a follow-up POST /marketplace." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_340px]">
        {/* ── Editor column ───────────────────────────────────────── */}
        <div className="space-y-6">
          <Section title="Metadata">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-[1fr_2fr]">
              <Field label="Name" helper="Required. Lowercased snake_case is conventional.">
                <input
                  className={inputCls}
                  placeholder="my_trend_scalp"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </Field>
              <Field label="Description" helper="One or two lines — shown on the marketplace card.">
                <textarea
                  className={`${inputCls} min-h-[70px] resize-y`}
                  placeholder="What does this strategy do and when is it well-suited?"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </Field>
            </div>
          </Section>

          <Section
            title="Code"
            right={
              <span className="inline-flex items-center gap-2 text-[11px] text-foreground/50">
                <code className="font-mono">{SIGNATURE}</code>
              </span>
            }
          >
            <div className="overflow-hidden rounded-md border border-white/10">
              <MonacoEditor
                height={520}
                theme="vs-dark"
                defaultLanguage="python"
                value={code}
                onChange={(v) => setCode(v ?? "")}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  fontFamily: "var(--font-geist-mono), ui-monospace, monospace",
                  lineNumbers: "on",
                  renderWhitespace: "selection",
                  scrollBeyondLastLine: false,
                  tabSize: 4,
                  insertSpaces: true,
                  wordWrap: "on",
                  automaticLayout: true,
                }}
              />
            </div>
          </Section>

          <LintPanel issues={issues} />
        </div>

        {/* ── Side column: guardrails + request preview ───────────── */}
        <aside className="lg:sticky lg:top-20 space-y-4 self-start">
          <StatusCard
            name={name.trim()}
            errCount={errCount}
            warnCount={warnCount}
            canSave={canSave}
          />

          <SandboxRef />

          <PublishCard publish={publish} setPublish={setPublish} />

          <details className="group rounded-xl border border-white/10 bg-black/20">
            <summary className="cursor-pointer px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-foreground/60 hover:text-foreground">
              Request body
            </summary>
            <pre className="max-h-80 overflow-auto rounded-b-xl px-4 pb-3 font-mono text-[11px] leading-relaxed text-foreground/70">
              {JSON.stringify(
                { ...payload, code_blob: "<" + code.length + " chars>" },
                null,
                2
              )}
            </pre>
          </details>
        </aside>
      </div>
    </div>
  )
}

// ── Side panels ─────────────────────────────────────────────────────────────

function StatusCard({
  name,
  errCount,
  warnCount,
  canSave,
}: {
  name: string
  errCount: number
  warnCount: number
  canSave: boolean
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <p className="text-[10px] uppercase tracking-wider text-foreground/40">Status</p>
      <p className="mt-1 font-mono text-sm text-foreground/80">{name || "<unnamed>"}</p>
      <div className="mt-3 space-y-1.5 text-xs">
        <Row
          ok={!!name}
          label="Name set"
          failHint="Required"
        />
        <Row
          ok={errCount === 0}
          label={errCount === 0 ? "No lint errors" : `${errCount} lint error${errCount > 1 ? "s" : ""}`}
          failHint="See panel below"
        />
        <Row ok warnHint={warnCount > 0 ? `${warnCount} warning${warnCount > 1 ? "s" : ""}` : undefined} label="Warnings" />
        <Row ok={canSave} label="Ready to save" failHint="Fix the items above" />
      </div>
    </div>
  )
}

function Row({
  ok,
  label,
  failHint,
  warnHint,
}: {
  ok: boolean
  label: string
  failHint?: string
  warnHint?: string
}) {
  const Icon = ok ? Check : X
  const tone = warnHint
    ? "text-yellow-400"
    : ok
      ? "text-[var(--color-teal)]"
      : "text-[var(--color-red-light)]"
  return (
    <div className="flex items-start gap-2">
      <Icon size={12} className={`mt-0.5 shrink-0 ${tone}`} />
      <span className="flex-1 text-foreground/70">{label}</span>
      {!ok && failHint && <span className="text-[10px] text-foreground/40">{failHint}</span>}
      {warnHint && <span className="text-[10px] text-yellow-400/80">{warnHint}</span>}
    </div>
  )
}

function SandboxRef() {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-[12px]">
      <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-foreground/60">
        <ShieldAlert size={12} className="text-[var(--color-orange)]" />
        Sandbox rules
      </p>
      <ul className="mt-3 space-y-3 text-foreground/70">
        <li>
          <p className="text-foreground/50">Allowed imports</p>
          <p className="mt-0.5 font-mono text-[11px]">{ALLOWED_IMPORTS.join(", ")}</p>
        </li>
        <li>
          <p className="text-foreground/50">Allowed builtins</p>
          <p className="mt-0.5 font-mono text-[11px] leading-relaxed">
            {ALLOWED_BUILTINS.join(", ")}
          </p>
        </li>
        <li>
          <p className="text-foreground/50">Forbidden names</p>
          <p className="mt-0.5 font-mono text-[11px] leading-relaxed text-[var(--color-red-light)]/80">
            {FORBIDDEN_NAMES.join(", ")}
          </p>
        </li>
        <li>
          <p className="text-foreground/50">Forbidden imports</p>
          <p className="mt-0.5 font-mono text-[11px] leading-relaxed text-[var(--color-red-light)]/80">
            {FORBIDDEN_MODULES.join(", ")}
          </p>
        </li>
        <li>
          <p className="text-foreground/50">Tick budget</p>
          <p className="mt-0.5 font-mono text-[11px]">
            {CPU_BUDGET_MS}ms CPU · {MEMORY_BUDGET_MB}MB memory
          </p>
        </li>
        <li>
          <p className="text-foreground/50">Must return</p>
          <p className="mt-0.5 font-mono text-[11px]">(signal: float, detail: str)</p>
          <p className="mt-1 text-[11px] text-foreground/40">
            Any other return shape is rejected at tick time; agent falls back to{" "}
            <code className="font-mono">simple_momentum</code>.
          </p>
        </li>
        <li>
          <p className="text-foreground/50">No access to</p>
          <p className="mt-0.5 text-[11px] text-foreground/60">
            network · filesystem · subprocess · agent env · user secrets · hub / user-server objects.
          </p>
        </li>
      </ul>
    </div>
  )
}

function PublishCard({
  publish,
  setPublish,
}: {
  publish: boolean
  setPublish: (v: boolean) => void
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
            <Upload size={13} className="text-[var(--color-orange)]" /> Publish to marketplace
          </p>
          <p className="mt-1 text-[11px] text-foreground/50">
            Makes this strategy installable by other users. 3+ reports in 7 days auto-hides it.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setPublish(!publish)}
          className={`relative h-5 w-9 shrink-0 rounded-full transition ${
            publish ? "bg-[var(--color-orange)]" : "bg-white/[0.08]"
          }`}
          aria-pressed={publish}
        >
          <span
            className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
              publish ? "translate-x-[18px]" : "translate-x-0.5"
            }`}
          />
        </button>
      </div>
    </div>
  )
}

function LintPanel({ issues }: { issues: LintIssue[] }) {
  if (issues.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-[var(--color-teal)]/30 bg-[var(--color-teal)]/5 p-3 text-xs text-[var(--color-teal)]">
        <Check size={14} />
        Lint clean — sandbox-compatible so far.{" "}
        <span className="ml-1 text-[var(--color-teal)]/70">
          (Server is the source of truth at save time.)
        </span>
      </div>
    )
  }
  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2.5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-foreground/60">
          Lint ({issues.length})
        </h3>
        <p className="text-[11px] text-foreground/40">
          Must define <code className="font-mono">{REQUIRED_FN}(plan, price_history, candles)</code>
        </p>
      </div>
      <ul className="divide-y divide-white/5 text-sm">
        {issues.map((i, idx) => (
          <li key={idx} className="flex items-start gap-3 px-4 py-2.5">
            {i.severity === "error" ? (
              <AlertTriangle size={14} className="mt-0.5 shrink-0 text-[var(--color-red-light)]" />
            ) : i.severity === "warn" ? (
              <AlertTriangle size={14} className="mt-0.5 shrink-0 text-yellow-400" />
            ) : (
              <Info size={14} className="mt-0.5 shrink-0 text-[var(--color-blue-light)]" />
            )}
            <div className="min-w-0 flex-1">
              <p className="text-foreground/80">{i.message}</p>
              <p className="mt-0.5 font-mono text-[11px] text-foreground/40">
                line {i.line}
                {i.token ? ` · ${i.token}` : ""}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ── Layout primitives ───────────────────────────────────────────────────────

function Section({
  title,
  right,
  children,
}: {
  title: string
  right?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
      <header className="mb-4 flex items-center justify-between border-b border-white/5 pb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-foreground/60">{title}</h3>
        {right}
      </header>
      {children}
    </section>
  )
}

function Field({
  label,
  helper,
  children,
}: {
  label: string
  helper?: string
  children: React.ReactNode
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-foreground/60">
        {label}
      </span>
      {children}
      {helper && <p className="mt-1.5 text-[11px] text-foreground/40">{helper}</p>}
    </label>
  )
}

const inputCls =
  "w-full rounded-md border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-foreground placeholder:text-foreground/30 focus:border-[var(--color-orange)]/50 focus:outline-none"
