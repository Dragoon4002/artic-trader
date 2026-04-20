"use client"

import { useState } from "react"
import Link from "next/link"
import { Library, Plus, Trash2, Upload, Code } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import {
  demoAuthoredStrategies,
  demoInstalledStrategies,
  DemoStrategy,
} from "@/lib/demo-data"

type Tab = "installed" | "authored"

const SOURCE_TONE: Record<DemoStrategy["source"], string> = {
  builtin: "border-white/15 bg-white/[0.04] text-foreground/70",
  marketplace: "border-[var(--color-blue-accent)]/30 bg-[var(--color-blue-accent)]/10 text-[var(--color-blue-light)]",
  authored: "border-[var(--color-orange)]/30 bg-[var(--color-orange)]/10 text-[var(--color-orange-text)]",
}

export default function StrategiesPage() {
  const [tab, setTab] = useState<Tab>("installed")
  const list = tab === "installed" ? demoInstalledStrategies : demoAuthoredStrategies
  return (
    <div className="space-y-8">
      <PageHeader
        title="Strategies"
        subtitle="Built-in, marketplace-installed, and your authored strategies."
        action={
          <Link
            href="/app/strategies/new"
            className="inline-flex items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] hover:bg-[var(--color-orange)]/20"
          >
            <Plus size={14} /> New strategy
          </Link>
        }
      />

      <PendingHub what="Installed + authored strategies are served from your user-server." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>
          {demoInstalledStrategies.length} installed · {demoAuthoredStrategies.length} authored (demo)
        </span>
      </div>

      <div className="flex items-center gap-1 border-b border-white/10">
        <TabBtn
          label={`Installed (${demoInstalledStrategies.length})`}
          active={tab === "installed"}
          onClick={() => setTab("installed")}
        />
        <TabBtn
          label={`Authored (${demoAuthoredStrategies.length})`}
          active={tab === "authored"}
          onClick={() => setTab("authored")}
        />
      </div>

      {list.length === 0 ? (
        <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.01] p-10 text-center">
          {tab === "installed" ? (
            <Library size={22} className="mx-auto text-[var(--color-orange)]" />
          ) : (
            <Upload size={22} className="mx-auto text-[var(--color-orange)]" />
          )}
          <p className="mt-4 text-sm text-foreground/60">
            {tab === "installed" ? "No strategies installed." : "No authored strategies."}
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-white/5 rounded-xl border border-white/10 bg-white/[0.02]">
          {list.map((s) => (
            <li
              key={s.id}
              className="flex items-start justify-between gap-4 p-4 transition hover:bg-white/[0.02]"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate font-mono text-sm font-semibold text-foreground">{s.name}</p>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${SOURCE_TONE[s.source]}`}
                  >
                    {s.source}
                  </span>
                  {s.installs != null && (
                    <span className="text-[11px] text-foreground/40">{s.installs} installs</span>
                  )}
                  {s.author && (
                    <span className="text-[11px] text-foreground/40">by {s.author}</span>
                  )}
                </div>
                <p className="mt-1.5 text-sm text-foreground/60">{s.description}</p>
                {s.updated_at && (
                  <p className="mt-1 font-mono text-[11px] text-foreground/40">
                    edited {s.updated_at.slice(0, 10)}
                  </p>
                )}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {tab === "authored" && (
                  <button
                    disabled
                    title="Hub auth wiring pending"
                    className="inline-flex cursor-not-allowed items-center gap-1 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-xs text-foreground/40"
                  >
                    <Code size={12} /> Edit
                  </button>
                )}
                {s.source !== "builtin" && (
                  <button
                    disabled
                    title="Hub auth wiring pending"
                    className="inline-flex cursor-not-allowed items-center gap-1 rounded-md border border-[var(--color-red)]/30 bg-white/[0.02] px-2.5 py-1.5 text-xs text-[var(--color-red-light)] opacity-60"
                  >
                    <Trash2 size={12} />
                    Remove
                  </button>
                )}
                {s.source === "authored" && (
                  <button
                    disabled
                    title="Hub auth wiring pending"
                    className="inline-flex cursor-not-allowed items-center gap-1 rounded-md border border-[var(--color-orange)]/30 bg-[var(--color-orange)]/5 px-2.5 py-1.5 text-xs text-[var(--color-orange-text)] opacity-70"
                  >
                    <Upload size={12} /> Publish
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "installed" && (
        <div className="flex justify-end">
          <Link
            href="/app/marketplace"
            className="text-xs text-foreground/50 underline-offset-4 hover:text-foreground hover:underline"
          >
            Browse marketplace →
          </Link>
        </div>
      )}
    </div>
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
