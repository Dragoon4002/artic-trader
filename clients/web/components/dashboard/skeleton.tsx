/** Thin skeleton placeholder. Use as the loading fallback for Query hooks. */
export function Skeleton({
  className = "",
  height,
}: {
  className?: string
  height?: number
}) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-white/[0.04] ${className}`}
      style={height ? { height } : undefined}
    />
  )
}
