"use client"

import Link from "next/link"
import { ChevronRight, Sparkles } from "lucide-react"
import { useOnboarding } from "@/hooks/use-onboarding"

/**
 * Passive banner shown on the dashboard while any onboarding step is
 * incomplete. Hides once all three are done. Linking to /app/onboarding is
 * the only affordance — nothing to dismiss.
 */
export function OnboardingBanner() {
  const { hydrated, allDone, completedCount, totalSteps } = useOnboarding()
  if (!hydrated || allDone) return null

  return (
    <Link
      href="/app/onboarding"
      className="focus-ring group flex items-center gap-3 rounded-2xl bg-[var(--color-accent-warm-soft)] p-5 transition hover:bg-[var(--color-accent-warm)]/18"
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-accent-warm)]/20 text-[var(--color-accent-warm)]">
        <Sparkles size={16} />
      </span>
      <div className="flex-1 text-sm">
        <p className="font-semibold tracking-tight text-foreground">
          Finish setting up
        </p>
        <p className="mt-0.5 text-xs text-foreground/65">
          {completedCount} of {totalSteps} steps complete · add LLM key, pick a
          strategy, create your first agent.
        </p>
      </div>
      <ChevronRight
        size={16}
        className="shrink-0 text-[var(--color-accent-warm)] transition group-hover:translate-x-0.5"
      />
    </Link>
  )
}
