"use client"

import { useMemo, useState } from "react"
import { Copy, Search } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { demoIndexer } from "@/lib/demo-data"

type Tab = "mine" | "all"

const KIND_TONE: Record<string, string> = {
  trades: "text-[var(--color-orange-text)] bg-[var(--color-orange)]/10 border-[var(--color-orange)]/30",
  supervise: "text-[var(--color-blue-light)] bg-[var(--color-blue-accent)]/10 border-[var(--color-blue-accent)]/30",
}

export default function IndexerPage() {
  const [tab, setTab] = useState<Tab>("mine")
  const [kind, setKind] = useState<"" | "trades" | "supervise">("")
  const [minAmount, setMinAmount] = useState("")

  const rows = useMemo(() => {
    let list = demoIndexer
    if (kind) list = list.filter((r) => r.kind === kind)
    if (minAmount) {
      const n = Number(minAmount)
      if (!Number.isNaN(n)) list = list.filter((r) => (r.amount_usdt ?? 0) >= n)
    }
    return list
  }, [kind, minAmount])

  return (
    <div className="space-y-8">
      <PageHeader
        title="Indexer"
        subtitle="On-chain tx mirror from every user-server. Read-only."
      />

      <PendingHub what="Rows stream from hub /indexer/tx; filters compose server-side." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>
          {rows.length} of {demoIndexer.length} demo rows shown
        </span>
      </div>

      <div className="flex items-center gap-1 border-b border-white/10">
        <TabBtn label="My txs" active={tab === "mine"} onClick={() => setTab("mine")} />
        <TabBtn label="All users" active={tab === "all"} onClick={() => setTab("all")} />
      </div>

      <section className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <Filter label="Agent">
            <input className={inputCls} placeholder="agent_id" />
          </Filter>
          <Filter label="Kind">
            <select
              className={inputCls}
              value={kind}
              onChange={(e) => setKind(e.target.value as "" | "trades" | "supervise")}
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

      <section className="rounded-xl border border-white/10 bg-white/[0.02]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-[11px] uppercase tracking-wide text-foreground/50">
              <th className="px-4 py-2.5">tx_hash</th>
              <th className="px-4 py-2.5">kind</th>
              <th className="px-4 py-2.5">amount</th>
              <th className="px-4 py-2.5">symbol</th>
              <th className="px-4 py-2.5">side</th>
              <th className="px-4 py-2.5">block</th>
              <th className="px-4 py-2.5">time</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-14 text-center text-foreground/40">
                  <div className="flex flex-col items-center gap-2">
                    <Search size={18} />
                    <p>No rows match current filters.</p>
                  </div>
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.tx_hash} className="border-b border-white/5 last:border-b-0">
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => navigator.clipboard.writeText(r.tx_hash)}
                      className="group inline-flex items-center gap-1.5 font-mono text-xs text-foreground/70 hover:text-foreground"
                      title="Copy tx hash"
                    >
                      {r.tx_hash}
                      <Copy size={11} className="opacity-0 transition group-hover:opacity-60" />
                    </button>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${KIND_TONE[r.kind]}`}
                    >
                      {r.kind}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-foreground/70">
                    {r.amount_usdt == null ? (
                      <span className="text-foreground/30">—</span>
                    ) : (
                      r.amount_usdt
                    )}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-foreground/70">{r.symbol}</td>
                  <td className="px-4 py-2.5">
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
                  <td className="px-4 py-2.5 font-mono text-[11px] text-foreground/50">
                    {r.block.toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-foreground/40">
                    {r.created_at.slice(5, 16).replace("T", " ")}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}

const inputCls =
  "w-full rounded-md border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-foreground placeholder:text-foreground/30 focus:border-[var(--color-orange)]/50 focus:outline-none"

function Filter({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-xs font-semibold uppercase tracking-wide text-foreground/50">
      <span className="mb-1.5 block">{label}</span>
      {children}
    </label>
  )
}

function TabBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`-mb-px border-b-2 px-4 py-2.5 text-sm transition ${
        active
          ? "border-[var(--color-orange)] text-foreground"
          : "border-transparent text-foreground/50 hover:text-foreground/80"
      }`}
    >
      {label}
    </button>
  )
}
