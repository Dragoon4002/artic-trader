"use client"

import { useState } from "react"
import { Check, Copy, Search } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useIndexer } from "@/hooks/use-queries"
import type { IndexerFilter } from "@/lib/schemas"

type Tab = "mine" | "all"

const KIND_TONE: Record<string, string> = {
  trades:
    "text-[var(--color-accent-warm)] bg-[var(--color-accent-warm-soft)]",
  supervise:
    "text-[var(--color-blue-light)] bg-[var(--color-blue-accent)]/12",
}

export default function IndexerPage() {
  const [tab, setTab] = useState<Tab>("mine")
  const [kind, setKind] = useState<"" | "trades" | "supervise">("")
  const [minAmount, setMinAmount] = useState("")

  const filter: IndexerFilter = {
    scope: tab,
    kind: kind || undefined,
    min_amount: minAmount ? Number(minAmount) : undefined,
  }
  const { data: rows = [], isLoading } = useIndexer(filter)

  return (
    <div className="space-y-10">
      <PageHeader
        title="Indexer"
        subtitle="On-chain tx mirror from every user-server. Read-only."
      />

      <PendingHub what="Rows stream from hub /indexer/tx; filters compose server-side." />

      <div className="flex items-center gap-2 text-xs text-foreground/55">
        <DemoBadge />
        <span>{rows.length} demo rows shown</span>
      </div>

      <div className="flex items-center gap-1 border-b border-[rgba(194,203,212,0.08)]">
        <TabBtn
          label="My txs"
          active={tab === "mine"}
          onClick={() => setTab("mine")}
        />
        <TabBtn
          label="All users"
          active={tab === "all"}
          onClick={() => setTab("all")}
        />
      </div>

      <section className="surface p-5 md:p-6">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5 md:gap-4">
          <Filter label="Agent">
            <input className={inputCls} placeholder="agent_id" />
          </Filter>
          <Filter label="Kind">
            <select
              className={inputCls}
              value={kind}
              onChange={(e) =>
                setKind(e.target.value as "" | "trades" | "supervise")
              }
            >
              <option value="">any</option>
              <option value="trades">trades</option>
              <option value="supervise">supervise</option>
            </select>
          </Filter>
          <Filter label="Min amount (USDT)">
            <input
              className={inputCls}
              type="number"
              placeholder="0"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
            />
          </Filter>
          <Filter label="From">
            <input className={inputCls} type="date" />
          </Filter>
          <Filter label="To">
            <input className={inputCls} type="date" />
          </Filter>
        </div>
      </section>

      <section className="surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--color-surface-sunken)]/50 text-left text-[11px] uppercase tracking-wider text-foreground/55">
                <th className="px-5 py-3 font-medium">tx_hash</th>
                <th className="px-5 py-3 font-medium">kind</th>
                <th className="px-5 py-3 font-medium">amount</th>
                <th className="px-5 py-3 font-medium">symbol</th>
                <th className="px-5 py-3 font-medium">side</th>
                <th className="px-5 py-3 font-medium">block</th>
                <th className="px-5 py-3 font-medium">time</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8">
                    <Skeleton height={120} />
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-5 py-16 text-center text-foreground/50"
                  >
                    <div className="flex flex-col items-center gap-2">
                      <Search size={18} />
                      <p>No rows match current filters.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr
                    key={r.tx_hash}
                    className="transition hover:bg-white/[0.02]"
                  >
                    <td className="px-5 py-3">
                      <CopyTx tx={r.tx_hash} />
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                          KIND_TONE[r.kind] ?? "bg-white/5 text-foreground/65"
                        }`}
                      >
                        {r.kind}
                      </span>
                    </td>
                    <td className="num-tabular px-5 py-3 font-mono text-foreground/80">
                      {r.amount_usdt == null ? (
                        <span className="text-foreground/30">—</span>
                      ) : (
                        r.amount_usdt
                      )}
                    </td>
                    <td className="px-5 py-3 font-mono text-foreground/80">
                      {r.symbol}
                    </td>
                    <td className="px-5 py-3">
                      {r.side ? (
                        <span
                          className={
                            r.side === "long"
                              ? "text-[var(--color-teal)]"
                              : "text-[var(--color-red-light)]"
                          }
                        >
                          {r.side}
                        </span>
                      ) : (
                        <span className="text-foreground/30">—</span>
                      )}
                    </td>
                    <td className="num-tabular px-5 py-3 font-mono text-[11px] text-foreground/50">
                      {r.block.toLocaleString()}
                    </td>
                    <td className="num-tabular px-5 py-3 font-mono text-[11px] text-foreground/50">
                      {r.created_at.slice(5, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function CopyTx({ tx }: { tx: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(tx)
        setCopied(true)
        setTimeout(() => setCopied(false), 1400)
      }}
      className="focus-ring group inline-flex items-center gap-1.5 rounded px-1 font-mono text-xs text-foreground/80 transition hover:text-foreground"
      aria-label={copied ? "Copied transaction hash" : "Copy transaction hash"}
    >
      <span className="max-w-[180px] truncate md:max-w-none">{tx}</span>
      {copied ? (
        <Check size={11} className="text-[var(--color-teal)]" />
      ) : (
        <Copy
          size={11}
          className="opacity-40 transition group-hover:opacity-85 group-focus-visible:opacity-85"
        />
      )}
    </button>
  )
}

const inputCls =
  "w-full rounded-md bg-[var(--color-surface-sunken)] px-3 py-2 text-sm text-foreground placeholder:text-foreground/30 ring-1 ring-inset ring-[rgba(194,203,212,0.10)] focus:outline-none focus:ring-[var(--color-accent-warm)]/55 focus:ring-2"

function Filter({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label className="block text-[11px] font-semibold uppercase tracking-wider text-foreground/55">
      <span className="mb-1.5 block">{label}</span>
      {children}
    </label>
  )
}

function TabBtn({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`focus-ring relative -mb-px px-4 py-2.5 text-sm transition-colors ${
        active
          ? "text-foreground"
          : "text-foreground/55 hover:text-foreground/85"
      }`}
    >
      {label}
      {active && (
        <span className="pointer-events-none absolute inset-x-4 -bottom-px h-[2px] rounded-full bg-[var(--color-accent-warm)]" />
      )}
    </button>
  )
}
