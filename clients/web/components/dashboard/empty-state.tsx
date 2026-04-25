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
    <div className="surface flex flex-col items-center justify-center p-14 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]">
        {icon}
      </div>
      <h2 className="mt-5 text-lg font-semibold tracking-tight text-foreground">
        {title}
      </h2>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-foreground/60">
        {body}
      </p>
      {cta && <div className="mt-6">{cta}</div>}
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
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="h-page text-foreground">{title}</h1>
        {subtitle && (
          <p className="mt-2 text-sm text-foreground/55">{subtitle}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
