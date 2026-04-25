"use client"

import Link from "next/link"
import { ArrowRight, Check, KeyRound, Library, Bot } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"
import { useOnboarding, type OnboardingStep } from "@/hooks/use-onboarding"

interface StepDef {
  key: OnboardingStep
  icon: React.ReactNode
  title: string
  body: string
  href: string
  cta: string
}

const STEPS: StepDef[] = [
  {
    key: "llm_key",
    icon: <KeyRound size={18} />,
    title: "Add an LLM key",
    body: "OpenAI, Anthropic, DeepSeek, or Gemini. Stored encrypted on the hub; decrypted only inside your VM.",
    href: "/app/settings",
    cta: "Add key",
  },
  {
    key: "strategy",
    icon: <Library size={18} />,
    title: "Pick a strategy",
    body: "Pool from the 30+ built-in quant strategies, or install one from the marketplace.",
    href: "/app/marketplace",
    cta: "Browse marketplace",
  },
  {
    key: "first_agent",
    icon: <Bot size={18} />,
    title: "Create your first agent",
    body: "Choose a symbol, set risk params, select LLM + strategy pool. Paper trading only in alpha.",
    href: "/app/agents/new",
    cta: "Create agent",
  },
]

export default function OnboardingPage() {
  const { completed, completedCount, totalSteps, allDone, setCompleted, reset } =
    useOnboarding()
  const pct = (completedCount / totalSteps) * 100

  return (
    <div className="space-y-10">
      <PageHeader
        title="Get set up"
        subtitle={
          allDone
            ? "All three done — jump into the dashboard."
            : `${completedCount} of ${totalSteps} complete · skip any, come back anytime.`
        }
        action={
          completedCount > 0 && (
            <button
              onClick={reset}
              className="focus-ring rounded-md bg-white/[0.04] px-3 py-1.5 text-xs text-foreground/75 transition hover:bg-white/[0.08] hover:text-foreground"
            >
              Reset
            </button>
          )
        }
      />

      <PendingHub what="Completion is currently tracked in localStorage; moves to hub on auth wiring." />

      <div className="space-y-2">
        <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-foreground/55">
          <span>Progress</span>
          <span className="num-tabular font-mono text-foreground/75">
            {completedCount} / {totalSteps}
          </span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-[var(--color-surface-sunken)]">
          <div
            className="h-full rounded-full bg-[var(--color-accent-warm)] transition-all duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <ol className="space-y-4">
        {STEPS.map((step, i) => {
          const done = completed[step.key]
          return (
            <li
              key={step.key}
              className={`flex flex-col gap-4 rounded-2xl p-6 transition md:flex-row md:items-center ${
                done
                  ? "bg-[var(--color-teal)]/[0.08]"
                  : "surface"
              }`}
            >
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                  done
                    ? "bg-[var(--color-teal)]/15 text-[var(--color-teal)]"
                    : "bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]"
                }`}
              >
                {done ? <Check size={18} /> : step.icon}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-foreground/50">
                    Step {i + 1}
                  </span>
                  {done && (
                    <span className="rounded-full bg-[var(--color-teal)]/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-teal)]">
                      Done
                    </span>
                  )}
                </div>
                <h3 className="mt-1 text-base font-semibold tracking-tight text-foreground">
                  {step.title}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-foreground/65">
                  {step.body}
                </p>
              </div>
              <div className="flex shrink-0 flex-row-reverse items-center gap-3 md:flex-col md:items-end">
                <Link
                  href={step.href}
                  className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-[var(--color-accent-warm)] px-4 py-2 text-xs font-semibold text-[var(--color-surface)] transition hover:bg-[var(--color-accent-warm-hover)]"
                >
                  {step.cta}
                  <ArrowRight size={12} />
                </Link>
                <button
                  onClick={() => setCompleted(step.key, !done)}
                  className="focus-ring rounded text-[10px] uppercase tracking-wider text-foreground/45 transition hover:text-foreground/80"
                >
                  {done ? "Mark undone" : "Mark done"}
                </button>
              </div>
            </li>
          )
        })}
      </ol>

      <div className="flex justify-end">
        <Link
          href="/app/agents"
          className={`focus-ring inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition ${
            allDone
              ? "bg-[var(--color-accent-warm)] font-semibold text-[var(--color-surface)] hover:bg-[var(--color-accent-warm-hover)]"
              : "text-foreground/55 hover:text-foreground"
          }`}
        >
          {allDone ? "Go to agents" : "Skip for now"}
          <ArrowRight size={13} />
        </Link>
      </div>
    </div>
  )
}
