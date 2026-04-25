"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowRight, Library, Plus, Trash2, Upload, Code } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { DemoBadge } from "@/components/dashboard/demo-badge"
import { Skeleton } from "@/components/dashboard/skeleton"
import { useStrategies } from "@/hooks/use-queries"
import type { Strategy, StrategySourceT } from "@/lib/schemas"
import { strategyStats } from "@/lib/demo-data"

type Tab = "installed" | "authored"

const SOURCE_TONE: Record<StrategySourceT, string> = {
  builtin: "bg-white/[0.05] text-foreground/75",
  marketplace:
    "bg-[var(--color-blue-accent)]/12 text-[var(--color-blue-light)]",
  authored:
    "bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]",
}

export default function StrategiesPage() {
  const [tab, setTab] = useState<Tab>("installed")
  const { data, isLoading } = useStrategies()
  const installed = data?.installed ?? []
  const authored = data?.authored ?? []
  const list = tab === "installed" ? installed : authored
  return (
    <div className="space-y-10">
      <PageHeader
        title="Strategies"
        subtitle="Built-in, marketplace-installed, and your authored strategies."
        action={
          <Link
            href="/app/strategies/new"
            className="focus-ring inline-flex items-center gap-2 rounded-md bg-[var(--color-accent-warm)] px-4 py-2 text-sm font-semibold text-[var(--color-surface)] shadow-[0_8px_24px_-12px_rgba(232,162,122,0.7)] transition hover:bg-[var(--color-accent-warm-hover)]"
          >
            <Plus size={14} /> New strategy
          </Link>
        }
      />

      <PendingHub what="Installed + authored strategies are served from your user-server." />

      <div className="flex items-center gap-2 text-xs text-foreground/55">
        <DemoBadge />
        <span>
          {installed.length} installed · {authored.length} authored (demo)
        </span>
      </div>

      <div className="flex items-center gap-1 border-b border-[rgba(194,203,212,0.08)]">
        <TabBtn
          label={`Installed (${installed.length})`}
          active={tab === "installed"}
          onClick={() => setTab("installed")}
        />
        <TabBtn
          label={`Authored (${authored.length})`}
          active={tab === "authored"}
          onClick={() => setTab("authored")}
        />
      </div>

      {isLoading ? (
        <Skeleton height={200} />
      ) : tab === "installed" && list.length > 0 ? (
        <StrategyCardGrid list={list} />
      ) : list.length === 0 ? (
        <div className="surface flex flex-col items-center justify-center p-14 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]">
            {tab === "installed" ? (
              <Library size={20} />
            ) : (
              <Upload size={20} />
            )}
          </div>
          <p className="mt-5 text-sm text-foreground/65">
            {tab === "installed"
              ? "No strategies installed."
              : "No authored strategies."}
          </p>
          <div className="mt-5">
            <Link
              href={
                tab === "installed" ? "/app/marketplace" : "/app/strategies/new"
              }
              className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-[var(--color-accent-warm)] px-4 py-2 text-xs font-semibold text-[var(--color-surface)] hover:bg-[var(--color-accent-warm-hover)]"
            >
              {tab === "installed" ? "Browse marketplace" : "Author one"}
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      ) : (
        <ul className="surface divide-y divide-[rgba(194,203,212,0.05)] overflow-hidden">
          {list.map((s) => (
            <li
              key={s.id}
              className="flex flex-col gap-4 p-5 transition hover:bg-white/[0.015] md:flex-row md:items-start md:justify-between"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="truncate font-mono text-sm font-semibold tracking-tight text-foreground">
                    {s.name}
                  </p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${SOURCE_TONE[s.source]}`}
                  >
                    {s.source}
                  </span>
                  {s.installs != null && (
                    <span className="num-tabular text-[11px] text-foreground/50">
                      {s.installs} installs
                    </span>
                  )}
                  {s.author && (
                    <span className="text-[11px] text-foreground/50">
                      by {s.author}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-foreground/65">
                  {s.description}
                </p>
                {s.updated_at && (
                  <p className="mt-1.5 font-mono text-[11px] text-foreground/45">
                    edited {s.updated_at.slice(0, 10)}
                  </p>
                )}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {tab === "authored" && (
                  <ActionBtn
                    disabled
                    icon={<Code size={12} />}
                    label="Edit"
                    tone="neutral"
                  />
                )}
                {s.source !== "builtin" && (
                  <ActionBtn
                    disabled
                    icon={<Trash2 size={12} />}
                    label="Remove"
                    tone="danger"
                  />
                )}
                {s.source === "authored" && (
                  <ActionBtn
                    disabled
                    icon={<Upload size={12} />}
                    label="Publish"
                    tone="accent"
                  />
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "installed" && list.length > 0 && (
        <div className="flex justify-end">
          <Link
            href="/app/marketplace"
            className="focus-ring inline-flex items-center gap-1.5 rounded text-xs text-foreground/55 transition hover:text-foreground"
          >
            Browse marketplace
            <ArrowRight size={12} />
          </Link>
        </div>
      )}
    </div>
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

function StrategyCardGrid({ list }: { list: Strategy[] }) {
  const stats = strategyStats()
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {list.map((s) => {
        const m = stats[s.name] ?? { uses: 0, success_rate: 0, creator_wallet: "init1artic...core00" }
        const uses = s.uses ?? m.uses
        const success = s.success_rate ?? m.success_rate
        const wallet = s.creator_wallet ?? s.author ?? m.creator_wallet
        const successPct = Math.round(success * 100)
        const successTone =
          success >= 0.6
            ? "text-[var(--color-teal-light)]"
            : success >= 0.45
              ? "text-foreground/80"
              : "text-[var(--color-red-light)]"
        return (
          <div
            key={s.id}
            className="surface group flex flex-col gap-4 p-5 transition hover:bg-white/[0.02]"
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="truncate font-mono text-sm font-semibold tracking-tight text-foreground">
                  {s.name}
                </p>
                <p className="mt-1.5 line-clamp-2 text-[13px] leading-snug text-foreground/55">
                  {s.description}
                </p>
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${SOURCE_TONE[s.source]}`}
              >
                {s.source}
              </span>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-3 border-t border-[rgba(194,203,212,0.08)] pt-4">
              <Stat label="Uses" value={String(uses)} />
              <Stat label="Success" value={`${successPct}%`} tone={successTone} />
            </div>

            {/* Footer — creator wallet */}
            <div className="flex items-center justify-between gap-2 border-t border-[rgba(194,203,212,0.08)] pt-3">
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-wider text-foreground/40">
                  Creator
                </p>
                <p className="truncate font-mono text-[12px] text-foreground/70">
                  {wallet}
                </p>
              </div>
              {s.source !== "builtin" && (
                <ActionBtn
                  disabled
                  icon={<Trash2 size={12} />}
                  label="Remove"
                  tone="danger"
                />
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-foreground/40">{label}</p>
      <p className={`num-tabular mt-1 text-lg font-semibold ${tone ?? "text-foreground"}`}>
        {value}
      </p>
    </div>
  )
}

function ActionBtn({
  icon,
  label,
  disabled,
  tone,
}: {
  icon: React.ReactNode
  label: string
  disabled?: boolean
  tone: "neutral" | "danger" | "accent"
}) {
  const base =
    "focus-ring inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium transition"
  const toneCls =
    tone === "danger"
      ? "bg-[var(--color-red)]/10 text-[var(--color-red-light)] hover:bg-[var(--color-red)]/15"
      : tone === "accent"
        ? "bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)] hover:bg-[var(--color-accent-warm)]/18"
        : "bg-white/[0.05] text-foreground/80 hover:bg-white/[0.08] hover:text-foreground"
  return (
    <button
      disabled={disabled}
      title={disabled ? "Hub auth wiring pending" : undefined}
      className={`${base} ${toneCls} ${disabled ? "btn-disabled" : ""}`}
    >
      {icon}
      {label}
    </button>
  )
}
