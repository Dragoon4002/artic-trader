"use client"

import { Coins } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useCredits, useLedger } from "@/hooks/use-queries"

type ToneKey = "halted" | "red" | "amber" | "green"

function balanceTone(balance: number): ToneKey {
  if (balance <= 0) return "halted"
  if (balance < 1) return "red"
  if (balance <= 10) return "amber"
  return "green"
}

const TONE: Record<ToneKey, { text: string; bg: string; label: string }> = {
  halted: {
    text: "text-foreground/55",
    bg: "bg-white/[0.05]",
    label: "halted",
  },
  red: {
    text: "text-[var(--color-red-light)]",
    bg: "bg-[var(--color-red)]/12",
    label: "red",
  },
  amber: {
    text: "text-[var(--color-amber)]",
    bg: "bg-[var(--color-amber)]/12",
    label: "amber",
  },
  green: {
    text: "text-[var(--color-teal)]",
    bg: "bg-[var(--color-teal)]/12",
    label: "green",
  },
}

const REASON_TONE: Record<string, string> = {
  tick_debit: "text-foreground/50",
  admin_grant: "text-[var(--color-teal)]",
  halt_refund: "text-[var(--color-blue-accent)]",
}

export default function CreditsPage() {
  const { data: credits, isLoading: creditsLoading } = useCredits()
  const { data: ledger = [], isLoading: ledgerLoading } = useLedger()
  const balance = credits?.balance_ah ?? 0
  const toneKey = balanceTone(balance)
  const tone = TONE[toneKey]

  return (
    <div className="space-y-10">
      <PageHeader
        title="Credits"
        subtitle="1 AH = 1 agent-hour. Hub debits 1/60 AH per alive agent per minute."
      />

      <PendingHub what="Balance + ledger stream from the hub credits tables." />

      <div className="flex items-center gap-2 text-xs text-foreground/55">
        <DemoBadge />
        <span>Showing fixture balance + {ledger.length} ledger entries.</span>
      </div>

      {creditsLoading ? (
        <Skeleton height={140} />
      ) : (
        <div className="surface p-6 md:p-8">
          <div className="flex flex-wrap items-center gap-5">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-full ${tone.bg}`}
            >
              <Coins size={24} className={tone.text} />
            </div>
            <div>
              <p className="label-xs">Balance</p>
              <p className="num-tabular mt-1.5 font-mono text-3xl font-semibold tracking-tight text-foreground">
                {balance.toFixed(3)}{" "}
                <span className="text-sm font-normal text-foreground/50">AH</span>
              </p>
            </div>
            <div className="ml-auto text-right text-xs">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ${tone.bg} ${tone.text}`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                {tone.label}
              </span>
              <p className="mt-2.5 text-foreground/50">
                Topups are admin-grant only in alpha.
              </p>
              <p className="mt-0.5 text-foreground/50">
                Stripe / on-chain topup ships in beta.
              </p>
            </div>
          </div>
        </div>
      )}

      <section className="surface overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4">
          <h3 className="text-[15px] font-semibold tracking-tight text-foreground">
            Ledger
          </h3>
          <span className="text-[11px] text-foreground/50">
            last {ledger.length} entries
          </span>
        </div>
        {ledgerLoading ? (
          <div className="p-5">
            <Skeleton height={140} />
          </div>
        ) : ledger.length === 0 ? (
          <p className="px-5 py-10 text-center text-sm text-foreground/50">
            No entries yet.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--color-surface-sunken)]/50 text-left text-[11px] uppercase tracking-wider text-foreground/55">
                <th className="px-6 py-2.5 font-medium">Δ</th>
                <th className="px-6 py-2.5 font-medium">Reason</th>
                <th className="px-6 py-2.5 font-medium">Agent</th>
                <th className="px-6 py-2.5 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((row) => (
                <tr
                  key={row.id}
                  className="transition hover:bg-white/[0.02]"
                >
                  <td
                    className={`num-tabular px-6 py-3 font-mono ${
                      row.delta > 0
                        ? "text-[var(--color-teal)]"
                        : row.delta < 0
                          ? "text-foreground/75"
                          : "text-foreground/50"
                    }`}
                  >
                    {row.delta >= 0
                      ? `+${row.delta.toFixed(3)}`
                      : row.delta.toFixed(3)}
                  </td>
                  <td
                    className={`px-6 py-3 font-mono text-[11px] uppercase tracking-wider ${
                      REASON_TONE[row.reason] ?? "text-foreground/50"
                    }`}
                  >
                    {row.reason}
                  </td>
                  <td className="px-6 py-3 font-mono text-[11px] text-foreground/50">
                    {row.agent_id ? `${row.agent_id.slice(0, 8)}…` : "—"}
                  </td>
                  <td className="num-tabular px-6 py-3 font-mono text-[11px] text-foreground/50">
                    {row.created_at.slice(5, 16).replace("T", " ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <ThresholdCard
          tone="green"
          range=">10 AH"
          hint="All good."
          active={toneKey === "green"}
        />
        <ThresholdCard
          tone="amber"
          range="1–10 AH"
          hint="Consider topping up."
          active={toneKey === "amber"}
        />
        <ThresholdCard
          tone="red"
          range="<1 AH"
          hint="Hub halts agents on 0."
          active={toneKey === "red"}
        />
      </div>
    </div>
  )
}

function ThresholdCard({
  tone,
  range,
  hint,
  active,
}: {
  tone: Exclude<ToneKey, "halted">
  range: string
  hint: string
  active: boolean
}) {
  const s = TONE[tone]
  return (
    <div
      className={`rounded-2xl p-5 transition ${
        active
          ? `${s.bg} ring-1 ring-current/10`
          : "bg-[var(--color-surface-elevated)]/70"
      }`}
    >
      <p
        className={`text-[11px] font-semibold uppercase tracking-widest ${s.text}`}
      >
        {s.label}
      </p>
      <p className="num-tabular mt-2 font-mono text-base text-foreground/90">
        {range}
      </p>
      <p className="mt-2 text-xs text-foreground/55">{hint}</p>
    </div>
  )
}
