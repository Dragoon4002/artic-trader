"use client"

import { AlertTriangle, Rabbit } from "lucide-react"
import { useWarnings } from "./warnings-context"

/**
 * Navbar chip that toggles PendingHub + any other UI warnings. Defaults to
 * OFF (hidden) so demo views stay clean; flip ON while doing integration
 * work to see what still needs wiring.
 */
export function WarningsToggle() {
  const { visible, toggle } = useWarnings()
  const Icon = visible ? AlertTriangle : Rabbit
  return (
    <button
      onClick={toggle}
      aria-pressed={visible}
      title={visible ? "Hide integration warnings" : "Show integration warnings"}
      className={`focus-ring inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition ${
        visible
          ? "bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]"
          : "bg-white/[0.04] text-foreground/70 hover:bg-white/[0.08] hover:text-foreground"
      }`}
    >
      <Icon size={13} />
      <span className="hidden font-semibold sm:inline">
        Warnings {visible ? "on" : "off"}
      </span>
    </button>
  )
}
