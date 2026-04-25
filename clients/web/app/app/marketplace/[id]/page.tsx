"use client"

import Link from "next/link"
import { use, useState } from "react"
import { ArrowLeft, Download, Flag } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { ReportDialog } from "@/components/marketplace/report-dialog"
import { useMarketplaceItem } from "@/hooks/use-queries"

export default function MarketplaceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const { data: item, isLoading } = useMarketplaceItem(id)
  const [reportOpen, setReportOpen] = useState(false)

  return (
    <div className="space-y-8">
      <Link
        href="/app/marketplace"
        className="inline-flex items-center gap-1.5 text-xs text-foreground/50 hover:text-foreground"
      >
        <ArrowLeft size={12} /> Back to marketplace
      </Link>

      <PageHeader
        title={item?.name ?? id}
        subtitle={
          item ? (
            <span className="inline-flex items-center gap-2">
              by <span className="font-mono text-foreground/70">{item.author}</span>
              <span className="text-foreground/30">·</span>
              <span>{item.installs} installs</span>
              <span className="text-foreground/30">·</span>
              <span
                className={
                  item.reports >= 3
                    ? "text-[var(--color-red-light)]"
                    : item.reports > 0
                      ? "text-yellow-400"
                      : ""
                }
              >
                {item.reports} reports
              </span>
              <span className="text-foreground/30">·</span>
              <DemoBadge />
            </span>
          ) : isLoading ? (
            <span className="text-foreground/40">Loading…</span>
          ) : (
            <>
              Unknown listing — this id isn&apos;t in the demo fixture set.{" "}
              <Link href="/app/marketplace" className="underline hover:text-foreground">
                browse all
              </Link>
            </>
          )
        }
        action={
          <div className="flex items-center gap-2">
            <button
              disabled
              title="Hub auth wiring pending"
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] opacity-50"
            >
              <Download size={14} /> Install
            </button>
            <button
              onClick={() => item && setReportOpen(true)}
              disabled={!item}
              className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-foreground/70 transition hover:border-[var(--color-red)]/30 hover:text-[var(--color-red-light)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Flag size={14} /> Report
            </button>
          </div>
        }
      />

      <PendingHub what="Strategy metadata + code blob load from the hub marketplace." />

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton height={120} />
          <Skeleton height={260} />
        </div>
      ) : (
        <>
          <section className="rounded-xl border border-white/10 bg-white/[0.02] p-6">
            <h3 className="mb-2 text-sm font-semibold text-foreground/80">Description</h3>
            <p className="text-sm text-foreground/70">
              {item?.description ??
                "Strategy metadata is served from the hub marketplace table. This placeholder stands in for any id not present in lib/demo-data.ts."}
            </p>
          </section>

          {item && (
            <section className="rounded-xl border border-white/10 bg-white/[0.02] p-6">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground/80">Code preview</h3>
                <span className="font-mono text-[11px] text-foreground/40">
                  created {item.created_at.slice(0, 10)}
                </span>
              </div>
              <pre className="max-h-96 overflow-auto rounded bg-black/40 p-4 font-mono text-xs leading-relaxed text-foreground/70">
                {item.code_preview}
              </pre>
              <p className="mt-3 text-[11px] text-foreground/40">
                Runs sandboxed: no filesystem, no network, no subprocess. 500ms CPU + 64MB memory caps.
              </p>
            </section>
          )}
        </>
      )}

      <ReportDialog
        open={reportOpen}
        strategyName={item?.name ?? id}
        onClose={() => setReportOpen(false)}
      />
    </div>
  )
}
