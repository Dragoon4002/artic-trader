/**
 * USD ↔ INIT conversion for dashboard display.
 *
 * Rate is configurable via NEXT_PUBLIC_USD_PER_INIT (e.g. 0.5 = 1 INIT == $0.5).
 * Default tracks Initia testnet/mainnet rough trading range. All numbers stored
 * server-side stay in USD (legacy field names use *_usdt) — this is a pure
 * presentation-layer conversion for the dashboard.
 */

const USD_PER_INIT = Number(process.env.NEXT_PUBLIC_USD_PER_INIT ?? "0.5")

/** Convert a USD value (or amount_usdt-style number) to INIT. */
export function usdToInit(usd: number | null | undefined): number {
  if (usd == null || !Number.isFinite(usd)) return 0
  if (USD_PER_INIT <= 0) return usd
  return usd / USD_PER_INIT
}

/** "1,234.56 INIT" — sign+commas, 2 decimals, INIT suffix. */
export function fmtInit(usd: number | null | undefined): string {
  const v = usdToInit(usd)
  const sign = v > 0 ? "+" : v < 0 ? "−" : ""
  const abs = Math.abs(v)
  return `${sign}${abs.toLocaleString(undefined, { maximumFractionDigits: 2 })} INIT`
}

/** Same as fmtInit but no sign prefix — for absolute values like balances. */
export function fmtInitAbs(usd: number | null | undefined): string {
  const v = usdToInit(usd)
  return `${v.toLocaleString(undefined, { maximumFractionDigits: 2 })} INIT`
}
