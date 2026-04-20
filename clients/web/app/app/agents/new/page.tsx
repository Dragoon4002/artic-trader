"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  Bot,
  Eye,
  EyeOff,
  Fuel,
  KeyRound,
  Play,
  ShieldAlert,
  Sparkles,
  Timer,
} from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import {
  AgentFormState,
  LLM_MODELS,
  LLM_PROVIDERS,
  LlmProvider,
  RISK_PROFILES,
  SYMBOLS,
  TIMEFRAMES,
  TP_SL_MODES,
  defaultAgentForm,
  toCreatePayload,
} from "@/lib/agent-form"

export default function NewAgentPage() {
  const [form, setForm] = useState<AgentFormState>(defaultAgentForm)
  const [showKey, setShowKey] = useState(false)
  const payload = useMemo(() => toCreatePayload(form), [form])

  const set = <K extends keyof AgentFormState>(k: K, v: AgentFormState[K]) =>
    setForm((f) => ({ ...f, [k]: v }))

  return (
    <div className="space-y-8">
      <Link
        href="/app/agents"
        className="inline-flex items-center gap-1.5 text-xs text-foreground/50 hover:text-foreground"
      >
        <ArrowLeft size={12} /> Back to agents
      </Link>

      <PageHeader
        title="New agent"
        subtitle="Every config the hub's CreateAgentRequest accepts. Paper trading only in alpha."
      />

      <PendingHub what="Submit sends a signed POST /api/agents with the body shown in the right panel." />

      <form
        onSubmit={(e) => e.preventDefault()}
        className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_360px]"
      >
        <div className="space-y-8">
          <Section icon={<Bot size={15} />} title="Identity" hint="Human name + which market it trades.">
            <Grid cols={2}>
              <Field label="Name">
                <input
                  className={inputCls}
                  placeholder="eg. BTC momentum"
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                />
              </Field>
              <Field label="Symbol" helper="Appended with USDT automatically (all 27 Pyth feeds).">
                <select
                  className={inputCls}
                  value={form.symbol as string}
                  onChange={(e) => set("symbol", e.target.value)}
                >
                  {SYMBOLS.map((s) => (
                    <option key={s} value={s}>
                      {s}USDT
                    </option>
                  ))}
                </select>
              </Field>
            </Grid>
          </Section>

          <Section icon={<Play size={15} />} title="Trading" hint="Position sizing + how often the loop ticks.">
            <Grid cols={2}>
              <Field label="Amount (USDT)">
                <input
                  className={inputCls}
                  type="number"
                  min={1}
                  step={10}
                  value={form.amount_usdt}
                  onChange={(e) => set("amount_usdt", Number(e.target.value))}
                />
              </Field>
              <Field label={`Leverage  ${form.leverage}×`}>
                <input
                  type="range"
                  min={1}
                  max={10}
                  step={1}
                  value={form.leverage}
                  onChange={(e) => set("leverage", Number(e.target.value))}
                  className="w-full accent-[var(--color-orange)]"
                />
                <p className="mt-1 text-[10px] text-foreground/40">Alpha caps at 10×.</p>
              </Field>
              <Field label="Risk profile" helper="Passed to the LLM planner.">
                <SegControl
                  value={form.risk_profile}
                  onChange={(v) => set("risk_profile", v)}
                  options={RISK_PROFILES}
                />
              </Field>
              <Field label="Primary timeframe" helper="Chart horizon for strategy + supervisor.">
                <SegControl
                  value={form.primary_timeframe}
                  onChange={(v) => set("primary_timeframe", v)}
                  options={TIMEFRAMES}
                />
              </Field>
              <Field label={`Poll interval  ${form.poll_seconds.toFixed(1)}s`}>
                <input
                  type="range"
                  min={0.5}
                  max={5}
                  step={0.1}
                  value={form.poll_seconds}
                  onChange={(e) => set("poll_seconds", Number(e.target.value))}
                  className="w-full accent-[var(--color-orange)]"
                />
              </Field>
              <Field label={`Supervisor interval  ${form.supervisor_interval}s`}>
                <input
                  type="range"
                  min={30}
                  max={300}
                  step={5}
                  value={form.supervisor_interval}
                  onChange={(e) => set("supervisor_interval", Number(e.target.value))}
                  className="w-full accent-[var(--color-orange)]"
                />
                <p className="mt-1 text-[10px] text-foreground/40">Frequency of LLM supervise calls.</p>
              </Field>
            </Grid>
          </Section>

          <Section
            icon={<ShieldAlert size={15} />}
            title="Risk controls"
            hint="TP/SL per trade, session-wide loss cap, mode."
          >
            <Grid cols={3}>
              <Field label="TP %" helper="Blank = no fixed target.">
                <input
                  className={inputCls}
                  type="number"
                  step={0.1}
                  placeholder="eg. 1.5"
                  value={form.tp_pct}
                  onChange={(e) => set("tp_pct", e.target.value)}
                />
              </Field>
              <Field label="SL %" helper="Blank = no fixed stop.">
                <input
                  className={inputCls}
                  type="number"
                  step={0.1}
                  placeholder="eg. 0.8"
                  value={form.sl_pct}
                  onChange={(e) => set("sl_pct", e.target.value)}
                />
              </Field>
              <Field label="TP/SL mode" helper="Dynamic = ATR-based, supervisor-adjustable.">
                <SegControl
                  value={form.tp_sl_mode}
                  onChange={(v) => set("tp_sl_mode", v)}
                  options={TP_SL_MODES}
                />
              </Field>
            </Grid>
            <div className="mt-5">
              <Field label={`Max session loss  ${(form.max_session_loss_pct * 100).toFixed(0)}%`}>
                <input
                  type="range"
                  min={1}
                  max={100}
                  step={1}
                  value={form.max_session_loss_pct * 100}
                  onChange={(e) =>
                    set("max_session_loss_pct", Number(e.target.value) / 100)
                  }
                  className="w-full accent-[var(--color-orange)]"
                />
                <p className="mt-1 text-[10px] text-foreground/40">
                  Hub halts the agent when cumulative session PnL drops past this threshold.
                </p>
              </Field>
            </div>
          </Section>

          <Section icon={<Sparkles size={15} />} title="LLM" hint="Provider + model + optional per-agent key override.">
            <Grid cols={2}>
              <Field label="Provider">
                <div className="grid grid-cols-4 gap-2">
                  {LLM_PROVIDERS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => {
                        set("llm_provider", p)
                        // sensible default model per provider
                        set("llm_model", LLM_MODELS[p][0])
                      }}
                      className={`rounded-md border px-2 py-2 text-xs font-semibold transition ${
                        form.llm_provider === p
                          ? "border-[var(--color-orange)]/60 bg-[var(--color-orange)]/10 text-[var(--color-orange-text)]"
                          : "border-white/10 bg-white/[0.02] text-foreground/60 hover:text-foreground"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Model" helper="Pick a suggestion or type any id the provider exposes.">
                <input
                  className={inputCls}
                  list="llm-models"
                  value={form.llm_model}
                  onChange={(e) => set("llm_model", e.target.value)}
                />
                <datalist id="llm-models">
                  {LLM_MODELS[form.llm_provider as LlmProvider].map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </Field>
            </Grid>
            <div className="mt-5">
              <Field
                label={
                  <span className="inline-flex items-center gap-1.5">
                    <KeyRound size={11} /> Per-agent API key override
                  </span>
                }
                helper="Leave blank to use the key stored in Settings. Encrypted before storage."
              >
                <div className="relative">
                  <input
                    className={`${inputCls} pr-10`}
                    type={showKey ? "text" : "password"}
                    placeholder="sk-…"
                    autoComplete="off"
                    value={form.llm_api_key}
                    onChange={(e) => set("llm_api_key", e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey((v) => !v)}
                    className="absolute inset-y-0 right-2 my-auto flex h-6 w-6 items-center justify-center rounded text-foreground/40 hover:text-foreground"
                    aria-label={showKey ? "Hide key" : "Show key"}
                  >
                    {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </Field>
            </div>
          </Section>

          <Section icon={<Timer size={15} />} title="Behavior" hint="Lifecycle flags.">
            <Grid cols={2}>
              <ToggleField
                label="Auto-start"
                helper="Spawn the container immediately after create."
                checked={form.auto_start}
                onChange={(v) => set("auto_start", v)}
              />
              <ToggleField
                label="Live mode"
                helper="Real exchange routing. Alpha-locked OFF."
                checked={form.live_mode}
                onChange={() => {}}
                disabled
              />
            </Grid>
          </Section>

          <div className="flex items-center justify-end gap-3">
            <Link
              href="/app/agents"
              className="rounded-md border border-white/10 bg-white/[0.02] px-4 py-2 text-sm font-semibold text-foreground/70 transition hover:text-foreground"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled
              title="Hub auth wiring pending"
              className="cursor-not-allowed rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] opacity-50"
            >
              {form.auto_start ? "Create + start" : "Create"}
            </button>
          </div>
        </div>

        <aside className="lg:sticky lg:top-20 self-start">
          <SummaryPanel form={form} payload={payload} />
        </aside>
      </form>
    </div>
  )
}

// ── Summary side panel ────────────────────────────────────────────────────

function SummaryPanel({
  form,
  payload,
}: {
  form: AgentFormState
  payload: ReturnType<typeof toCreatePayload>
}) {
  const name = form.name.trim() || "Unnamed Agent"
  const risky =
    form.leverage >= 8 ||
    (form.tp_pct && Number(form.tp_pct) < 0.3) ||
    form.max_session_loss_pct > 0.5
  return (
    <div className="space-y-4 rounded-xl border border-white/10 bg-white/[0.02] p-5 text-sm">
      <div>
        <p className="text-[10px] uppercase tracking-wider text-foreground/40">Preview</p>
        <p className="mt-1 font-semibold text-foreground">{name}</p>
        <p className="font-mono text-xs text-foreground/50">{payload.symbol}</p>
      </div>

      <div className="space-y-1.5 border-t border-white/10 pt-3 text-xs">
        <Row k="Amount" v={`${form.amount_usdt} USDT`} />
        <Row k="Leverage" v={`${form.leverage}×`} />
        <Row k="Risk" v={form.risk_profile} />
        <Row k="Timeframe" v={form.primary_timeframe} />
        <Row k="Poll" v={`${form.poll_seconds.toFixed(1)}s`} />
        <Row k="Supervisor" v={`${form.supervisor_interval}s`} />
        <Row
          k="TP / SL"
          v={
            `${form.tp_pct || "—"}% / ${form.sl_pct || "—"}%` +
            (form.tp_sl_mode === "dynamic" ? " (dyn)" : "")
          }
        />
        <Row k="Session cap" v={`${(form.max_session_loss_pct * 100).toFixed(0)}%`} />
        <Row k="LLM" v={`${form.llm_provider} · ${form.llm_model || "—"}`} />
        <Row k="BYOK" v={form.llm_api_key ? "overridden" : "use stored"} />
        <Row k="Auto-start" v={form.auto_start ? "yes" : "no"} />
        <Row k="Mode" v={form.live_mode ? "LIVE" : "paper"} />
      </div>

      {risky && (
        <div className="flex items-start gap-2 rounded-md border border-yellow-500/30 bg-yellow-500/5 p-3 text-[11px] text-yellow-400/90">
          <Fuel size={12} className="mt-0.5 shrink-0" />
          <span>Aggressive config. Supervisor may halt early on drawdown.</span>
        </div>
      )}

      <details className="group rounded-md border border-white/10 bg-black/20">
        <summary className="cursor-pointer px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-foreground/50 hover:text-foreground">
          Request body
        </summary>
        <pre className="max-h-72 overflow-auto rounded-b-md px-3 pb-3 font-mono text-[11px] leading-relaxed text-foreground/70">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </details>
    </div>
  )
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-foreground/50">{k}</span>
      <span className="truncate text-right font-mono text-foreground/80">{v}</span>
    </div>
  )
}

// ── Layout primitives ─────────────────────────────────────────────────────

function Section({
  icon,
  title,
  hint,
  children,
}: {
  icon: React.ReactNode
  title: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
      <header className="mb-4 flex items-start justify-between gap-4 border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white/[0.04] text-[var(--color-orange)]">
            {icon}
          </span>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        </div>
        {hint && <p className="max-w-xs text-right text-[11px] text-foreground/40">{hint}</p>}
      </header>
      {children}
    </section>
  )
}

function Grid({ cols, children }: { cols: number; children: React.ReactNode }) {
  const c = cols === 3 ? "md:grid-cols-3" : "md:grid-cols-2"
  return <div className={`grid grid-cols-1 gap-5 ${c}`}>{children}</div>
}

function Field({
  label,
  helper,
  children,
}: {
  label: React.ReactNode
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

function ToggleField({
  label,
  helper,
  checked,
  onChange,
  disabled,
}: {
  label: string
  helper?: string
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
}) {
  return (
    <div
      className={`flex items-start justify-between rounded-md border border-white/10 bg-white/[0.02] p-4 ${disabled ? "opacity-60" : ""}`}
    >
      <div className="min-w-0 pr-4">
        <p className="text-sm font-semibold text-foreground/90">{label}</p>
        {helper && <p className="mt-0.5 text-[11px] text-foreground/50">{helper}</p>}
      </div>
      <button
        type="button"
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          checked ? "bg-[var(--color-orange)]" : "bg-white/[0.08]"
        } ${disabled ? "cursor-not-allowed" : ""}`}
        aria-pressed={checked}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  )
}

function SegControl<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T
  onChange: (v: T) => void
  options: readonly T[]
}) {
  return (
    <div className="grid grid-flow-col gap-1 rounded-md border border-white/10 bg-white/[0.02] p-1">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          onClick={() => onChange(o)}
          className={`rounded px-2 py-1.5 text-xs font-semibold capitalize transition ${
            value === o
              ? "bg-[var(--color-orange)]/20 text-[var(--color-orange-text)]"
              : "text-foreground/60 hover:text-foreground"
          }`}
        >
          {o}
        </button>
      ))}
    </div>
  )
}

const inputCls =
  "w-full rounded-md border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-foreground placeholder:text-foreground/30 focus:border-[var(--color-orange)]/50 focus:outline-none"
