"use client"

import { useMemo, useState } from "react"
import { Copy, Send, ArrowDownToLine } from "lucide-react"
import { parseEther } from "viem"
import { useSendTransaction } from "wagmi"
import { useChainWallet, useWithdrawChainWallet } from "@/hooks/use-queries"

export function ChainWalletCard() {
  const { data, isLoading, refetch } = useChainWallet()
  const { sendTransactionAsync, isPending: topupPending } = useSendTransaction()
  const withdrawMut = useWithdrawChainWallet()

  const [topupAmount, setTopupAmount] = useState("0.5")
  const [withdrawTo, setWithdrawTo] = useState("")
  const [withdrawAmount, setWithdrawAmount] = useState("")
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastTx, setLastTx] = useState<string | null>(null)

  const runoutLabel = useMemo(() => {
    if (!data?.runout_at) return "—"
    const d = new Date(data.runout_at)
    const days = (d.getTime() - Date.now()) / 86_400_000
    return `${d.toLocaleDateString()} (~${days.toFixed(1)}d)`
  }, [data?.runout_at])

  if (isLoading) {
    return <div className="surface p-6 text-sm text-foreground/40">Loading wallet…</div>
  }
  if (!data) return null

  const copy = async () => {
    if (!data.address) return
    await navigator.clipboard.writeText(data.address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const onTopup = async () => {
    setError(null); setLastTx(null)
    if (!data.address) return
    try {
      const hash = await sendTransactionAsync({
        to: data.address as `0x${string}`,
        value: parseEther(topupAmount as `${number}`),
      })
      setLastTx(hash)
      setTimeout(() => refetch(), 4000)
    } catch (e) {
      setError(String((e as Error)?.message ?? e))
    }
  }

  const onWithdraw = async () => {
    setError(null); setLastTx(null)
    try {
      const r = await withdrawMut.mutateAsync({ to: withdrawTo, amount: withdrawAmount })
      setLastTx(r.tx_hash)
    } catch (e) {
      setError(String((e as Error)?.message ?? e))
    }
  }

  const lowBalance = Number(data.balance_og) < Number(data.threshold_og)

  return (
    <section className="surface p-6">
      <header className="mb-4 flex items-center justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-foreground/55">
          Agent Gas Wallet
        </h3>
        {lowBalance && (
          <span className="rounded-full bg-[var(--color-red)]/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-red-light)]">
            Below {data.threshold_og} OG — agents cannot start
          </span>
        )}
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Kv label="Address" value={
            <span className="inline-flex items-center gap-1.5">
              <span className="font-mono text-xs">{data.address ?? "—"}</span>
              <button onClick={copy} className="text-foreground/40 hover:text-foreground" title="Copy">
                <Copy size={12} />
              </button>
              {copied && <span className="text-[10px] text-[var(--color-teal)]">copied</span>}
            </span>
          } />
          <Kv label="Balance" value={
            <span className={lowBalance ? "text-[var(--color-red-light)]" : "text-[var(--color-teal)]"}>
              {Number(data.balance_og).toFixed(4)} OG
            </span>
          } />
          <Kv label="Min to start" value={`${data.threshold_og} OG`} />
        </div>
        <div className="space-y-2">
          <Kv label="Burn rate" value={`${Number(data.burn_rate_og_per_day).toFixed(4)} OG/day`} />
          <Kv label="Cost / tx" value={`${Number(data.cost_per_tx_og).toFixed(6)} OG`} />
          <Kv label="Forecast runout" value={runoutLabel} />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-white/[0.06] p-4">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-foreground/55">Top up</p>
          <div className="flex gap-2">
            <input
              type="number" step="0.1" min="0"
              value={topupAmount}
              onChange={(e) => setTopupAmount(e.target.value)}
              className="w-full rounded-md bg-white/[0.04] px-3 py-1.5 font-mono text-xs"
              placeholder="OG amount"
            />
            <button
              onClick={onTopup}
              disabled={topupPending || !data.address}
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--color-teal)]/15 px-3 py-1.5 text-xs font-semibold text-[var(--color-teal)] hover:bg-[var(--color-teal)]/25 disabled:opacity-50"
            >
              <Send size={12} />
              {topupPending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-white/[0.06] p-4">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-foreground/55">Withdraw</p>
          <div className="space-y-2">
            <input
              value={withdrawTo}
              onChange={(e) => setWithdrawTo(e.target.value)}
              placeholder="Destination 0x…"
              className="w-full rounded-md bg-white/[0.04] px-3 py-1.5 font-mono text-xs"
            />
            <div className="flex gap-2">
              <input
                type="number" step="0.1" min="0"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                placeholder="OG amount"
                className="w-full rounded-md bg-white/[0.04] px-3 py-1.5 font-mono text-xs"
              />
              <button
                onClick={onWithdraw}
                disabled={withdrawMut.isPending || !withdrawTo || !withdrawAmount}
                className="inline-flex items-center gap-1.5 rounded-md bg-[var(--color-accent-warm)]/15 px-3 py-1.5 text-xs font-semibold text-[var(--color-accent-warm)] hover:bg-[var(--color-accent-warm)]/25 disabled:opacity-50"
              >
                <ArrowDownToLine size={12} />
                {withdrawMut.isPending ? "Sending…" : "Withdraw"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {(error || lastTx) && (
        <div className="mt-4 text-xs">
          {error && <p className="text-[var(--color-red-light)]">Error: {error}</p>}
          {lastTx && (
            <p className="text-foreground/60">
              Tx: <span className="font-mono">{lastTx.slice(0, 18)}…</span>
            </p>
          )}
        </div>
      )}
    </section>
  )
}

function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[rgba(194,203,212,0.04)] py-2 text-sm last:border-b-0">
      <span className="text-foreground/55">{label}</span>
      <span className="font-mono text-foreground/90">{value}</span>
    </div>
  )
}
