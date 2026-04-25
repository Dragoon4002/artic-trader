"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { Menu, X } from "lucide-react"
import { ConnectButton } from "@/components/wallet/connect-button"
import { CreditsWidget } from "@/components/dashboard/credits-widget"
import { WarningsToggle } from "@/components/dashboard/warnings-toggle"

const NAV = [
  { href: "/app/agents", label: "Agents" },
  { href: "/app/strategies", label: "Strategies" },
  { href: "/app/marketplace", label: "Marketplace" },
  { href: "/app/credits", label: "Credits" },
  { href: "/app/indexer", label: "Indexer" },
  { href: "/app/settings", label: "Settings" },
]

export function DashboardHeader() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    setMobileOpen(false)
  }, [pathname])

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden"
      return () => {
        document.body.style.overflow = ""
      }
    }
  }, [mobileOpen])

  return (
    <header className="sticky top-0 z-40 bg-[var(--color-surface)]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-15 max-w-[88rem] items-center justify-between px-5 md:px-8">
        <div className="flex items-center gap-10">
          <Link
            href="/app"
            className="font-heading text-[17px] font-semibold tracking-tight text-foreground"
          >
            Artic
          </Link>
          <nav className="hidden items-center gap-0.5 md:flex">
            {NAV.map((item) => {
              const active = pathname?.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative rounded-md px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "text-foreground"
                      : "text-foreground/55 hover:text-foreground"
                  }`}
                >
                  {item.label}
                  {active && (
                    <span className="pointer-events-none absolute inset-x-3 -bottom-[13px] h-[2px] rounded-full bg-[var(--color-accent-warm)]" />
                  )}
                </Link>
              )
            })}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 md:flex">
            <WarningsToggle />
            <CreditsWidget />
          </div>
          <ConnectButton />
          <button
            type="button"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
            className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md bg-white/[0.04] text-foreground/80 hover:bg-white/[0.08] md:hidden"
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>
      {/* Hairline divider — single pixel, low contrast, sits below content */}
      <div className="h-px w-full bg-[rgba(194,203,212,0.06)]" />

      {/* Mobile drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 top-[60px] z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
          role="presentation"
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <nav
            className="relative mx-4 mt-3 rounded-2xl bg-[var(--color-surface-raised)] p-2 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <ul className="flex flex-col">
              {NAV.map((item) => {
                const active = pathname?.startsWith(item.href)
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center justify-between rounded-md px-3 py-3 text-sm transition-colors ${
                        active
                          ? "bg-[var(--color-accent-warm-soft)] text-[var(--color-accent-warm)]"
                          : "text-foreground/75 hover:bg-white/[0.05] hover:text-foreground"
                      }`}
                    >
                      <span>{item.label}</span>
                      {active && (
                        <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-accent-warm)]" />
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
            <div className="mt-2 flex items-center justify-between gap-2 border-t border-[rgba(194,203,212,0.06)] px-2 py-3">
              <WarningsToggle />
              <CreditsWidget />
            </div>
          </nav>
        </div>
      )}
    </header>
  )
}
