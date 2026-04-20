import { FlaskConical } from "lucide-react"

/**
 * Small pill marking any section populated from lib/demo-data.ts. Lets a
 * viewer tell synthetic fixtures apart from real hub data at a glance.
 */
export function DemoBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-yellow-500/30 bg-yellow-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-yellow-400">
      <FlaskConical size={10} />
      demo
    </span>
  )
}
