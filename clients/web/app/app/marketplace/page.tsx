"use client"

import { useState } from "react"
import Link from "next/link"
import { Store, Upload, Flag } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useMarketplace } from "@/hooks/use-queries"
import type { MarketplaceSort } from "@/lib/schemas"

const SORTS: { key: MarketplaceSort; label: string }[] = [
  { key: "installs", label: "Most installed" },
  { key: "recent", label: "Newest" },
  { key: "reports", label: "Most reported" },
]

export default function MarketplacePage() {
  const [sort, setSort] = useState<MarketplaceSort>("installs")
  const { data: sorted = [], isLoading } = useMarketplace(sort)

  return (
    <div className="space-y-10">
      <PageHeader
        title="Strategy marketplace"
        subtitle="Browse, install, and publish Python strategies. All code runs in RestrictedPython."
        action={
          <button
            disabled
            title="Hub auth wiring pending"
            className="btn-disabled inline-flex items-center gap-2 rounded-md bg-white/[0.04] px-4 py-2 text-sm text-foreground/55"
          >
            <Upload size={14} /> Publish
          </button>
        }
      />

      <PendingHub what="Listings come from the hub marketplace tables." />

      <div className="flex items-center gap-2 text-xs text-foreground/55">
        <DemoBadge />
        <span>{sorted.length} demo listings</span>
      </div>

      <div className="flex items-center gap-1 border-b border-[rgba(194,203,212,0.08)]">
        {SORTS.map((s) => (
          <button
            key={s.key}
            onClick={() => setSort(s.key)}
            className={`focus-ring relative -mb-px px-4 py-2.5 text-sm transition-colors ${
              sort === s.key
                ? "text-foreground"
                : "text-foreground/55 hover:text-foreground/85"
            }`}
          >
            {s.label}
            {sort === s.key && (
              <span className="pointer-events-none absolute inset-x-4 -bottom-px h-[2px] rounded-full bg-[var(--color-accent-warm)]" />
            )}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={180} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sorted.map((s) => (
            <Link
              key={s.id}
              href={`/app/marketplace/${s.id}`}
              className="hover-lift surface group flex h-full flex-col justify-between p-5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-warm)]/60"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm font-semibold tracking-tight text-foreground">
                      {s.name}
                    </p>
                    <p className="mt-0.5 text-[11px] text-foreground/50">
                      by {s.author}
                    </p>
                  </div>
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)] opacity-60 transition group-hover:opacity-100">
                    <Store size={14} />
                  </span>
                </div>
                <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-foreground/65">
                  {s.description}
                </p>
              </div>
              <div className="mt-5 flex items-center justify-between pt-3 text-[11px]">
                <span className="num-tabular text-foreground/50">
                  {s.installs.toLocaleString()} installs
                </span>
                <ReportBadge reports={s.reports} />
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="surface-sunken flex items-start gap-3 p-4 text-xs text-foreground/60">
        <Flag
          size={14}
          className="mt-0.5 shrink-0 text-[var(--color-red-light)]"
        />
        <div>
          <p className="font-semibold text-foreground/85">Reporting</p>
          <p className="mt-1 leading-relaxed">
            Any user can flag a strategy. 3+ reports in 7 days auto-hides it
            pending admin review.
          </p>
        </div>
      </div>
    </div>
  )
}

function ReportBadge({ reports }: { reports: number }) {
  if (reports >= 3) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-red)]/12 px-2 py-0.5 text-[var(--color-red-light)]">
        <Flag size={10} />
        {reports}
      </span>
    )
  }
  if (reports > 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-amber)]/12 px-2 py-0.5 text-[var(--color-amber)]">
        <Flag size={10} />
        {reports}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-foreground/35">
      <Flag size={10} />
      {reports}
    </span>
  )
}
