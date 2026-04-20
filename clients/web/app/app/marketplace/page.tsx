"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { Store, Upload, Flag } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { demoMarketplace } from "@/lib/demo-data"

const SORTS = [
  { key: "installs", label: "Most installed" },
  { key: "recent", label: "Newest" },
  { key: "reports", label: "Most reported" },
] as const

type SortKey = (typeof SORTS)[number]["key"]

export default function MarketplacePage() {
  const [sort, setSort] = useState<SortKey>("installs")
  const sorted = useMemo(() => {
    const copy = [...demoMarketplace]
    if (sort === "installs") copy.sort((a, b) => b.installs - a.installs)
    if (sort === "reports") copy.sort((a, b) => b.reports - a.reports)
    if (sort === "recent")
      copy.sort((a, b) => b.created_at.localeCompare(a.created_at))
    return copy
  }, [sort])

  return (
    <div className="space-y-8">
      <PageHeader
        title="Strategy marketplace"
        subtitle="Browse, install, and publish Python strategies. All code runs in RestrictedPython."
        action={
          <button
            disabled
            title="Hub auth wiring pending"
            className="inline-flex cursor-not-allowed items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-foreground/40"
          >
            <Upload size={14} /> Publish
          </button>
        }
      />

      <PendingHub what="Listings come from the hub marketplace tables." />

      <div className="flex items-center gap-2 text-xs text-foreground/50">
        <DemoBadge />
        <span>{demoMarketplace.length} demo listings</span>
      </div>

      <div className="flex items-center gap-1 border-b border-white/10">
        {SORTS.map((s) => (
          <button
            key={s.key}
            onClick={() => setSort(s.key)}
            className={`-mb-px border-b-2 px-4 py-2.5 text-sm transition ${
              sort === s.key
                ? "border-[var(--color-orange)] text-foreground"
                : "border-transparent text-foreground/50 hover:text-foreground/80"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((s) => (
          <Link
            key={s.id}
            href={`/app/marketplace/${s.id}`}
            className="group flex h-full flex-col justify-between rounded-xl border border-white/10 bg-white/[0.02] p-5 transition hover:border-[var(--color-orange)]/40"
          >
            <div>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-mono text-sm font-semibold text-foreground">{s.name}</p>
                  <p className="mt-0.5 text-[11px] text-foreground/40">by {s.author}</p>
                </div>
                <Store size={16} className="shrink-0 text-foreground/20 transition group-hover:text-[var(--color-orange)]" />
              </div>
              <p className="mt-3 line-clamp-3 text-sm text-foreground/60">{s.description}</p>
            </div>
            <div className="mt-5 flex items-center justify-between border-t border-white/5 pt-3 text-[11px]">
              <span className="text-foreground/40">{s.installs} installs</span>
              <span
                className={
                  s.reports >= 3
                    ? "inline-flex items-center gap-1 text-[var(--color-red-light)]"
                    : s.reports > 0
                      ? "inline-flex items-center gap-1 text-yellow-400"
                      : "text-foreground/30"
                }
              >
                <Flag size={10} />
                {s.reports}
              </span>
            </div>
          </Link>
        ))}
      </div>

      <div className="rounded-md border border-white/10 bg-white/[0.02] p-4 text-xs text-foreground/50">
        <div className="flex items-start gap-2">
          <Flag size={14} className="mt-0.5 shrink-0 text-[var(--color-red-light)]" />
          <div>
            <p className="font-semibold text-foreground/70">Reporting</p>
            <p className="mt-1 leading-relaxed">
              Any user can flag a strategy. 3+ reports in 7 days auto-hides it pending admin review.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
