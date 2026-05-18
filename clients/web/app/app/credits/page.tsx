"use client"

import { useMemo, useState } from "react"
import { Coins, Filter, Info, Sparkles, Zap } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useCredits, useLedger } from "@/hooks/use-queries"

type ToneKey = "halted" | "red" | "amber" | "green"
type ReasonFilter = "all" | "tick_debit" | "admin_grant" | "halt_refund"

function balanceTone(balance: number): ToneKey {
  if (balance <= 0) return "halted"
  if (balance < 1) return "red"
  if (balance <= 10) return "amber"
  return "green"
}

const TONE: Record<ToneKey, { text: string; bg: string; ring: string; label: string }> = {
  halted: {
    text: "text-foreground/55",
    bg: "bg-white/[0.05]",
    ring: "ring-white/10",
    label: "halted",
  },
  red: {
    text: "text-[var(--color-red-light)]",
    bg: "bg-[var(--color-red)]/12",
    ring: "ring-[var(--color-red)]/30",
    label: "critical",
  },
  amber: {
    text: "text-[var(--color-amber)]",
    bg: "bg-[var(--color-amber)]/12",
    ring: "ring-[var(--color-amber)]/30",
    label: "low",
  },
  green: {
    text: "text-[var(--color-teal)]",
    bg: "bg-[var(--color-teal)]/12",
    ring: "ring-[var(--color-teal)]/25",
    label: "healthy",
  },
}

const REASON_LABEL: Record<string, string> = {
  tick_debit: "Tick debit",
  admin_grant: "Admin grant",
  halt_refund: "Halt refund",
}

const REASON_TONE: Record<string, { text: string; bg: string; dot: string }> = {
  tick_debit: {
    text: "text-foreground/70",
    bg: "bg-white/[0.04]",
    dot: "bg-foreground/40",
  },
  admin_grant: {
    text: "text-[var(--color-teal)]",
    bg: "bg-[var(--color-teal)]/12",
    dot: "bg-[var(--color-teal)]",
  },
  halt_refund: {
    text: "text-[var(--color-blue-accent)]",
    bg: "bg-[var(--color-blue-accent)]/12",
    dot: "bg-[var(--color-blue-accent)]",
  },
}

const QUOTA_AH = 100
const STORAGE_QUOTA_MB = 512
const SHOW_CREDITS = false

export default function CreditsPage() {
  const { data: credits, isLoading: creditsLoading } = useCredits()
  const { data: ledger = [], isLoading: ledgerLoading } = useLedger()
  const [filter, setFilter] = useState<ReasonFilter>("all")

  const balance = credits?.balance_ah ?? 0
  const toneKey = balanceTone(balance)
  const tone = TONE[toneKey]

  const { spent, granted, burnRate } = useMemo(() => {
    let s = 0
    let g = 0
    for (const r of ledger) {
      if (r.delta < 0) s += -r.delta
      else g += r.delta
    }
    const tickEntries = ledger.filter((r) => r.reason === "tick_debit")
    const tickSum = tickEntries.reduce((a, r) => a + -r.delta, 0)
    const rate = tickEntries.length ? tickSum / tickEntries.length : 0
    return { spent: s, granted: g, burnRate: rate }
  }, [ledger])

  const quotaPct = Math.min(100, (spent / QUOTA_AH) * 100)
  const storageUsedMb = 184
  const storagePct = (storageUsedMb / STORAGE_QUOTA_MB) * 100

  const filteredLedger = useMemo(
    () => (filter === "all" ? ledger : ledger.filter((r) => r.reason === filter)),
    [ledger, filter],
  )

  return (
    <div className="space-y-10">
      <PageHeader
        title="Credits"
        subtitle="1 AH = 1 agent-hour. Hub debits 1/60 AH per alive agent per minute."
      />

      {!SHOW_CREDITS && (
        <section className="surface flex flex-col items-center justify-center gap-3 p-16 text-center">
          <span className="rounded-full bg-[var(--color-accent-warm)]/15 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-accent-warm)]">
            Coming soon
          </span>
          <p className="text-sm text-foreground/55">Credits ledger ships next release.</p>
        </section>
      )}

      {SHOW_CREDITS && (<>
      <PendingHub what="Balance + ledger stream from the hub credits tables." />

      {/* <div className="flex items-center gap-2 text-xs text-foreground/55">
        <DemoBadge />
        <span>Showing fixture balance + {ledger.length} ledger entries.</span>
      </div> */}

      {/* Overview — balance card + usage card */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        {creditsLoading ? (
          <div className="lg:col-span-2">
            <Skeleton height={180} />
          </div>
        ) : (
          <div className="surface relative overflow-hidden p-6 md:p-7 lg:col-span-2">
            <div
              aria-hidden
              className={`pointer-events-none absolute -right-16 -top-16 h-44 w-44 rounded-full blur-3xl ${tone.bg}`}
            />
            <div className="relative flex items-start justify-between">
              <div>
                <div className="flex items-center gap-1.5">
                  <p className="label-xs">Current balance</p>
                  <BalanceInfoTooltip toneKey={toneKey} />
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span
                    className={`num-tabular font-mono text-4xl font-semibold tracking-tight ${tone.text}`}
                  >
                    {balance.toFixed(3)}
                  </span>
                  <span className="text-sm font-medium text-foreground/55">AH</span>
                </div>
                <p className="mt-1.5 text-xs text-foreground/50">
                  ≈ {(balance * 60).toFixed(0)} agent-minutes remaining
                </p>
              </div>
              {/* <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ring-1 ${tone.bg} ${tone.text} ${tone.ring}`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${tone.text} bg-current`} />
                {tone.label}
              </span> */}
            </div>

            <div className="relative mt-6 flex flex-wrap items-center gap-2">
              <button
                disabled
                className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-full bg-foreground/90 px-3.5 py-1.5 text-xs font-semibold text-background opacity-70 transition hover:opacity-90"
              >
                <Sparkles size={13} />
                Top up
                <span className="ml-1 rounded-full bg-background/15 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                  beta
                </span>
              </button>
              <span className="text-[11px] text-foreground/45">
                Stripe / on-chain topup ships in beta · alpha is admin-grant only
              </span>
            </div>
          </div>
        )}

        {/* Usage Summary */}
        <div className="surface p-6 md:p-7 lg:col-span-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-tight text-foreground">
              Usage summary
            </h3>
            <span className="text-[11px] text-foreground/45">last 30 days</span>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
            <UsageMeter
              icon={<Coins size={14} />}
              label="Agent-hours used"
              valueLeft={spent.toFixed(2)}
              valueRight={`${QUOTA_AH} AH`}
              pct={quotaPct}
              barClass="bg-[var(--color-blue-accent)]"
            />
            <UsageMeter
              icon={<Zap size={14} />}
              label="Sandbox storage"
              valueLeft={`${storageUsedMb} MB`}
              valueRight={`${STORAGE_QUOTA_MB} MB`}
              pct={storagePct}
              barClass="bg-[var(--color-amber)]"
            />
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3 border-t border-white/[0.06] pt-4">
            <Stat label="Granted" value={granted.toFixed(3)} suffix="AH" />
            <Stat
              label="Spent"
              value={spent.toFixed(3)}
              suffix="AH"
              tone="text-foreground/75"
            />
            <Stat
              label="Avg debit"
              value={burnRate.toFixed(4)}
              suffix="AH/tick"
              tone="text-foreground/75"
            />
          </div>
        </div>
      </section>

      {/* Ledger */}
      <section className="surface overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div>
            <h3 className="text-[15px] font-semibold tracking-tight text-foreground">
              Ledger
            </h3>
            <p className="mt-0.5 text-[11px] text-foreground/50">
              Last {filteredLedger.length} of {ledger.length} entries
            </p>
          </div>
          <div className="flex items-center gap-1.5 rounded-full bg-white/5 p-1">
            <FilterChip active={filter === "all"} onClick={() => setFilter("all")}>
              <Filter size={11} /> All
            </FilterChip>
            <FilterChip
              active={filter === "tick_debit"}
              onClick={() => setFilter("tick_debit")}
            >
              Debits
            </FilterChip>
            <FilterChip
              active={filter === "admin_grant"}
              onClick={() => setFilter("admin_grant")}
            >
              Grants
            </FilterChip>
            <FilterChip
              active={filter === "halt_refund"}
              onClick={() => setFilter("halt_refund")}
            >
              Refunds
            </FilterChip>
          </div>
        </div>

        {ledgerLoading ? (
          <div className="p-5">
            <Skeleton height={140} />
          </div>
        ) : filteredLedger.length === 0 ? (
          <p className="px-5 py-10 text-center text-sm text-foreground/50">
            No entries match this filter.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-transparent text-left text-[11px] uppercase tracking-wider text-foreground/55">
                <th className="px-6 py-2.5 font-medium">Time</th>
                <th className="px-6 py-2.5 font-medium">Reason</th>
                <th className="px-6 py-2.5 font-medium">Agent</th>
                <th className="px-6 py-2.5 text-right font-medium">Δ AH</th>
              </tr>
            </thead>
            <tbody>
              {filteredLedger.map((row) => {
                const rt = REASON_TONE[row.reason] ?? REASON_TONE.tick_debit
                return (
                  <tr
                    key={row.id}
                    className="border-t border-white/[0.04] transition hover:bg-white/[0.02]"
                  >
                    <td className="num-tabular px-6 py-3.5 font-mono text-[11px] text-foreground/55">
                      {row.created_at.slice(5, 16).replace("T", " ")}
                    </td>
                    <td className="px-6 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${rt.bg} ${rt.text}`}
                      >
                        <span className={`h-1 w-1 rounded-full ${rt.dot}`} />
                        {REASON_LABEL[row.reason] ?? row.reason}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-[11px] text-foreground/55">
                      {row.agent_id ? `${row.agent_id.slice(0, 8)}…` : "—"}
                    </td>
                    <td
                      className={`num-tabular px-6 py-3.5 text-right font-mono text-sm font-semibold ${
                        row.delta > 0
                          ? "text-[var(--color-teal)]"
                          : row.delta < 0
                            ? "text-foreground/85"
                            : "text-foreground/45"
                      }`}
                    >
                      {row.delta >= 0
                        ? `+${row.delta.toFixed(3)}`
                        : row.delta.toFixed(3)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </section>
      </>)}

    </div>
  )
}

function BalanceInfoTooltip({ toneKey }: { toneKey: ToneKey }) {
  const rows: Array<{ tone: Exclude<ToneKey, "halted">; range: string; hint: string }> = [
    { tone: "green", range: ">10 AH", hint: "All agents run freely." },
    { tone: "amber", range: "1–10 AH", hint: "Consider topping up soon." },
    { tone: "red", range: "<1 AH", hint: "Hub halts agents at 0." },
  ]
  return (
    <span className="group/info relative inline-flex">
      <button
        type="button"
        aria-label="Balance info"
        className="inline-flex h-4 w-4 items-center justify-center rounded-full text-foreground/45 transition hover:text-foreground/80 focus:text-foreground/80 focus:outline-none"
      >
        <Info size={12} />
      </button>
      <div
        role="tooltip"
        className="pointer-events-none invisible absolute left-0 top-full z-50 mt-2 w-80 -translate-y-1 rounded-xl border border-white/10 bg-[var(--color-surface-raised)] p-4 text-left opacity-0 shadow-xl shadow-black/40 transition-all duration-150 group-hover/info:visible group-hover/info:translate-y-0 group-hover/info:opacity-100 group-focus-within/info:visible group-focus-within/info:translate-y-0 group-focus-within/info:opacity-100"
      >
        <p className="text-xs leading-relaxed text-foreground/75">
          Hub debits 1/60 AH per alive agent per minute. Balance refunds on halt; agents
          stop automatically on 0.
        </p>

        <div className="mt-3 border-t border-white/[0.06] pt-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-foreground/55">
            Halt thresholds
          </p>
          <ul className="space-y-1.5">
            {rows.map((r) => {
              const t = TONE[r.tone]
              const active = toneKey === r.tone
              return (
                <li
                  key={r.tone}
                  className="flex items-start gap-2 text-[11px] text-foreground/65"
                >
                  <span
                    className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${t.text} bg-current`}
                  />
                  <span className="flex-1">
                    <span className={`font-mono font-semibold ${t.text}`}>
                      {r.range}
                    </span>{" "}
                    <span className="text-foreground/55">— {r.hint}</span>
                    {active && (
                      <span className="ml-1 rounded-full bg-white/[0.08] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-foreground/70">
                        now
                      </span>
                    )}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>

        <div className="mt-3 border-t border-white/[0.06] pt-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-foreground/55">
            Topup methods
          </p>
          <ul className="space-y-1 text-[11px] text-foreground/65">
            <li className="flex items-baseline gap-2">
              <span className="text-[var(--color-teal)]">•</span>
              <span>
                <span className="font-semibold text-foreground/85">Admin grant</span> —
                operator-initiated. Active in alpha.
              </span>
            </li>
            <li className="flex items-baseline gap-2">
              <span className="text-foreground/40">•</span>
              <span>
                <span className="font-semibold text-foreground/85">Card / Stripe</span>{" "}
                — recurring or one-shot fiat. Ships in beta.
              </span>
            </li>
            <li className="flex items-baseline gap-2">
              <span className="text-foreground/40">•</span>
              <span>
                <span className="font-semibold text-foreground/85">On-chain</span> —
                USDC / INIT deposit to hub vault. Ships in beta.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </span>
  )
}

function UsageMeter({
  icon,
  label,
  valueLeft,
  valueRight,
  pct,
  barClass,
}: {
  icon: React.ReactNode
  label: string
  valueLeft: string
  valueRight: string
  pct: number
  barClass: string
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] text-foreground/55">
        <span className="inline-flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        <span className="num-tabular font-mono">{pct.toFixed(0)}%</span>
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="num-tabular font-mono text-xl font-semibold tracking-tight text-foreground">
          {valueLeft}
        </span>
        <span className="text-xs text-foreground/45">/ {valueRight}</span>
      </div>
      <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.05]">
        <div
          className={`h-full rounded-full ${barClass} transition-all`}
          style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
        />
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  suffix,
  tone = "text-foreground",
}: {
  label: string
  value: string
  suffix: string
  tone?: string
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-foreground/45">{label}</p>
      <p className="num-tabular mt-1 font-mono text-base font-semibold">
        <span className={tone}>{value}</span>{" "}
        <span className="text-[10px] font-normal text-foreground/45">{suffix}</span>
      </p>
    </div>
  )
}

function FilterChip({
  active,
  children,
  onClick,
}: {
  active: boolean
  children: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-medium transition ${
        active
          ? "bg-foreground/90 text-background"
          : "text-foreground/60 hover:text-foreground"
      }`}
    >
      {children}
    </button>
  )
}

