"use client"

import Link from "next/link"
import { Plus } from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"
import { displayName } from "@/lib/identity"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { demoAgents, AgentStatus } from "@/lib/demo-data"

const STATUS_TONE: Record<AgentStatus, string> = {
  alive: "text-[var(--color-teal)] bg-[var(--color-teal)]/10 border-[var(--color-teal)]/30",
  starting: "text-[var(--color-orange)] bg-[var(--color-orange)]/10 border-[var(--color-orange)]/30",
  stopped: "text-foreground/50 bg-white/[0.04] border-white/10",
  error: "text-[var(--color-red-light)] bg-[var(--color-red)]/10 border-[var(--color-red)]/30",
  halted: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
}

export default function AgentsPage() {
  const { address, username } = useWallet()
  return (
    <div className="space-y-8">
      <PageHeader
        title="Your agents"
        subtitle={
          <>
            Signed in as <span className="text-foreground/80">{displayName(address, username)}</span>
          </>
        }
        action={
          <Link
            href="/app/agents/new"
            className="inline-flex items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] hover:bg-[var(--color-orange)]/20"
          >
            <Plus size={16} />
            New agent
          </Link>
        }
      />

      <PendingHub what="Agent list comes from GET /api/v1/u/agents." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>Showing {demoAgents.length} synthetic agents from lib/demo-data.ts.</span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {demoAgents.map((a) => {
          const pnl = a.unrealised_pnl
          return (
            <Link
              key={a.id}
              href={`/app/agents/${a.id}`}
              className="group rounded-xl border border-white/10 bg-white/[0.02] p-5 transition hover:border-[var(--color-orange)]/40"
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-foreground">{a.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-foreground/50">{a.symbol}</p>
                </div>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${STATUS_TONE[a.status]}`}
                >
                  {a.status}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <Kv label="Price" value={a.price.toLocaleString()} />
                <Kv
                  label="Side"
                  value={
                    a.side === "flat" ? (
                      <span className="text-foreground/40">flat</span>
                    ) : a.side === "long" ? (
                      <span className="text-[var(--color-teal)]">long</span>
                    ) : (
                      <span className="text-[var(--color-red-light)]">short</span>
                    )
                  }
                />
                <Kv
                  label="Unrealised"
                  value={
                    pnl == null ? (
                      <span className="text-foreground/40">—</span>
                    ) : pnl >= 0 ? (
                      <span className="text-[var(--color-teal)]">+{pnl.toFixed(2)}</span>
                    ) : (
                      <span className="text-[var(--color-red-light)]">{pnl.toFixed(2)}</span>
                    )
                  }
                />
                <Kv label="Strategy" value={<span className="font-mono">{a.strategy}</span>} />
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-[11px] text-foreground/40">
                <span className="font-mono">
                  {a.llm_provider} · {a.llm_model}
                </span>
                <span>
                  {a.amount_usdt} USDT · {a.leverage}×
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-foreground/40">{label}</span>
      <span className="text-sm text-foreground/80">{value}</span>
    </div>
  )
}
