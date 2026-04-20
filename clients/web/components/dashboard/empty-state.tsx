import type { ReactNode } from "react"

export function EmptyState({
  icon,
  title,
  body,
  cta,
}: {
  icon: ReactNode
  title: string
  body: ReactNode
  cta?: ReactNode
}) {
  return (
    <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.01] p-12 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white/[0.03]">
        {icon}
      </div>
      <h2 className="mt-5 text-lg font-semibold">{title}</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm text-foreground/60">{body}</p>
      {cta && <div className="mt-5">{cta}</div>}
    </div>
  )
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="mb-8 flex items-start justify-between gap-6">
      <div>
        <h1 className="font-heading text-3xl font-semibold">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-foreground/60">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
