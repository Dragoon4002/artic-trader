"use client"

import { Coins } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { demoCreditBalance, demoLedger } from "@/lib/demo-data"

function balanceTone(balance: number) {
  if (balance <= 0) return { label: "halted", color: "#9CA3AF" }
  if (balance < 1) return { label: "red", color: "var(--color-red)" }
  if (balance <= 10) return { label: "amber", color: "var(--color-orange)" }
  return { label: "green", color: "var(--color-teal)" }
}

const REASON_TONE: Record<string, string> = {
  tick_debit: "text-foreground/50",
  admin_grant: "text-[var(--color-teal)]",
  halt_refund: "text-[var(--color-blue-accent)]",
}

export default function CreditsPage() {
  const balance = demoCreditBalance
  const tone = balanceTone(balance)
  return (
    <div className="space-y-8">
      <PageHeader
        title="Credits"
        subtitle="1 AH = 1 agent-hour. Hub debits 1/60 AH per alive agent per minute."
      />

      <PendingHub what="Balance + ledger stream from the hub credits tables." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>Showing fixture balance + {demoLedger.length} ledger entries.</span>
      </div>

      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-8">
        <div className="flex items-center gap-4">
          <div
            className="flex h-14 w-14 items-center justify-center rounded-full"
            style={{ background: `${tone.color}22` }}
          >
            <Coins size={26} style={{ color: tone.color }} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-foreground/50">Balance</p>
            <p className="mt-1 font-mono text-3xl font-semibold text-foreground">
              {balance.toFixed(3)} <span className="text-sm text-foreground/40">AH</span>
            </p>
          </div>
          <div className="ml-auto text-right text-xs">
            <p
              className="font-semibold uppercase tracking-wide"
              style={{ color: tone.color }}
            >
              {tone.label}
            </p>
            <p className="mt-1 text-foreground/40">Topups are admin-grant only in alpha.</p>
            <p className="mt-0.5 text-foreground/40">Stripe / on-chain topup ships in beta.</p>
          </div>
        </div>
      </div>

      <section className="rounded-xl border border-white/10 bg-white/[0.02]">
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
          <h3 className="text-sm font-semibold text-foreground/80">Ledger</h3>
          <span className="text-[11px] text-foreground/40">last {demoLedger.length} entries</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wide text-foreground/50">
              <th className="px-5 py-2">Δ</th>
              <th className="px-5 py-2">Reason</th>
              <th className="px-5 py-2">Agent</th>
              <th className="px-5 py-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {demoLedger.map((row) => (
              <tr key={row.id} className="border-b border-white/5 last:border-b-0">
                <td
                  className={`px-5 py-2.5 font-mono ${
                    row.delta >= 0 ? "text-[var(--color-teal)]" : "text-foreground/70"
                  }`}
                >
                  {row.delta >= 0 ? `+${row.delta.toFixed(3)}` : row.delta.toFixed(3)}
                </td>
                <td
                  className={`px-5 py-2.5 font-mono text-[11px] uppercase tracking-wider ${REASON_TONE[row.reason] ?? "text-foreground/50"}`}
                >
                  {row.reason}
                </td>
                <td className="px-5 py-2.5 font-mono text-[11px] text-foreground/50">
                  {row.agent_id ? `${row.agent_id.slice(0, 8)}…` : "—"}
                </td>
                <td className="px-5 py-2.5 font-mono text-[11px] text-foreground/40">
                  {row.created_at.slice(5, 16).replace("T", " ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <ThresholdCard label="Green" range=">10 AH" hint="All good." color="var(--color-teal)" active={tone.label === "green"} />
        <ThresholdCard
          label="Amber"
          range="1-10 AH"
          hint="Consider topping up."
          color="var(--color-orange)"
          active={tone.label === "amber"}
        />
        <ThresholdCard
          label="Red"
          range="<1 AH"
          hint="Hub halts agents on 0."
          color="var(--color-red)"
          active={tone.label === "red"}
        />
      </div>
    </div>
  )
}

function ThresholdCard({
  label,
  range,
  hint,
  color,
  active,
}: {
  label: string
  range: string
  hint: string
  color: string
  active: boolean
}) {
  return (
    <div
      className="rounded-xl border p-4 transition"
      style={{
        borderColor: active ? color : `${color}44`,
        background: active ? `${color}10` : "rgba(255,255,255,0.02)",
      }}
    >
      <p className="text-xs font-semibold uppercase" style={{ color }}>
        {label}
      </p>
      <p className="mt-1 font-mono text-sm text-foreground/80">{range}</p>
      <p className="mt-2 text-xs text-foreground/50">{hint}</p>
    </div>
  )
}
