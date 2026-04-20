"use client"

import Link from "next/link"
import { Check, KeyRound, Library, Bot } from "lucide-react"
import { PageHeader } from "@/components/dashboard/empty-state"
import { PendingHub } from "@/components/dashboard/pending-hub"

const STEPS = [
  {
    icon: <KeyRound size={18} />,
    title: "Add an LLM key",
    body: "OpenAI, Anthropic, DeepSeek, or Gemini. Stored encrypted on the hub; decrypted only inside your VM.",
    href: "/app/settings",
    cta: "Add key",
  },
  {
    icon: <Library size={18} />,
    title: "Pick a strategy",
    body: "Pool from the 30+ built-in quant strategies, or install one from the marketplace.",
    href: "/app/marketplace",
    cta: "Browse marketplace",
  },
  {
    icon: <Bot size={18} />,
    title: "Create your first agent",
    body: "Choose a symbol, set risk params, select LLM + strategy pool. Paper trading only in alpha.",
    href: "/app/agents/new",
    cta: "Create agent",
  },
]

export default function OnboardingPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Get set up"
        subtitle="Three quick steps. Skip any — this page stays until all three are done."
      />

      <PendingHub what="Step completion is tracked server-side." />

      <ol className="space-y-3">
        {STEPS.map((step, i) => (
          <li
            key={step.title}
            className="flex items-start gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-5"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/[0.04] text-[var(--color-orange)]">
              {step.icon}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-foreground/40">Step {i + 1}</span>
                <Check size={12} className="text-foreground/20" />
              </div>
              <h3 className="mt-1 font-semibold">{step.title}</h3>
              <p className="mt-1 text-sm text-foreground/60">{step.body}</p>
            </div>
            <Link
              href={step.href}
              className="shrink-0 self-center rounded-md border border-white/10 bg-white/[0.03] px-4 py-2 text-xs font-semibold transition hover:border-[var(--color-orange)]/40"
            >
              {step.cta}
            </Link>
          </li>
        ))}
      </ol>

      <div className="flex justify-end">
        <Link
          href="/app/agents"
          className="text-xs text-foreground/50 underline-offset-4 hover:text-foreground/80 hover:underline"
        >
          Skip for now →
        </Link>
      </div>
    </div>
  )
}
