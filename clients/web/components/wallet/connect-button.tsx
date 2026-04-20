"use client"

import { useEffect, useRef, useState } from "react"
import { Wallet, Zap, Copy, LogOut, ExternalLink, ChevronDown } from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"
import { displayName, shortenAddr } from "@/lib/identity"
import { CHAIN_ID } from "@/lib/chain"

export function ConnectButton() {
  const { address, username, isConnected, openConnect, openWallet, disconnect, autoSign } = useWallet()
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onClickOutside)
    return () => document.removeEventListener("mousedown", onClickOutside)
  }, [])

  const copyAddress = async () => {
    if (!address) return
    await navigator.clipboard.writeText(address)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isAutoSignEnabled = !!autoSign?.isEnabledByChain?.[CHAIN_ID]
  const label = displayName(address, username)

  if (!isConnected) {
    return (
      <button
        onClick={openConnect}
        className="inline-flex items-center gap-2 rounded-md border border-[var(--color-orange)]/40 bg-[var(--color-orange)]/10 px-4 py-2 text-sm font-semibold text-[var(--color-orange-text)] transition hover:bg-[var(--color-orange)]/20 hover:border-[var(--color-orange)]/70"
      >
        <Wallet size={16} />
        Connect Wallet
      </button>
    )
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-foreground transition hover:border-[var(--color-orange)]/40 hover:bg-white/[0.05]"
      >
        <span className="h-2 w-2 rounded-full bg-[var(--color-teal)]" aria-hidden />
        <span className="font-mono">{label}</span>
        {isAutoSignEnabled && <Zap size={12} className="text-yellow-400" />}
        <ChevronDown size={14} className={`opacity-60 transition ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-[calc(100%+6px)] z-50 w-64 overflow-hidden rounded-md border border-white/10 bg-[var(--color-surface)] shadow-xl">
          <div className="border-b border-white/10 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded bg-white/[0.04]">
                <Wallet size={15} className="text-[var(--color-orange)]" />
              </div>
              <div className="min-w-0 flex-1">
                {username ? (
                  <>
                    <p className="truncate text-sm font-semibold text-[var(--color-orange-text)]">{label}</p>
                    <p className="mt-0.5 truncate font-mono text-xs text-foreground/40">
                      {shortenAddr(address)}
                    </p>
                  </>
                ) : (
                  <p className="truncate font-mono text-sm text-foreground/70">{shortenAddr(address)}</p>
                )}
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-teal)]" />
              <span className="text-[var(--color-teal)]">Connected</span>
              {isAutoSignEnabled && (
                <>
                  <span className="text-foreground/20">·</span>
                  <Zap size={10} className="text-yellow-400" />
                  <span className="text-yellow-400/80">Auto-Sign</span>
                </>
              )}
            </div>
          </div>

          <div>
            <MenuItem onClick={copyAddress} icon={<Copy size={14} />}>
              {copied ? "Copied!" : "Copy address"}
            </MenuItem>
            <MenuItem
              onClick={() => {
                openWallet()
                setOpen(false)
              }}
              icon={<ExternalLink size={14} />}
            >
              Wallet manager
            </MenuItem>
            <MenuItem
              onClick={() => {
                disconnect()
                setOpen(false)
              }}
              icon={<LogOut size={14} />}
              variant="danger"
            >
              Disconnect
            </MenuItem>
          </div>
        </div>
      )}
    </div>
  )
}

function MenuItem({
  children,
  icon,
  onClick,
  variant = "default",
}: {
  children: React.ReactNode
  icon: React.ReactNode
  onClick: () => void
  variant?: "default" | "danger"
}) {
  const color =
    variant === "danger"
      ? "text-[var(--color-red-light)] hover:bg-[var(--color-red)]/10 hover:text-[var(--color-red)]"
      : "text-foreground/70 hover:bg-white/[0.04] hover:text-foreground"
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-3 border-b border-white/5 px-4 py-3 text-left text-sm transition last:border-b-0 ${color}`}
    >
      {icon}
      {children}
    </button>
  )
}
