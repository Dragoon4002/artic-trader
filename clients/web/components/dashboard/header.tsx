"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { ConnectButton } from "@/components/wallet/connect-button"

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
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-[var(--color-surface)]/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/app" className="font-heading text-lg font-semibold">
            Artic
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => {
              const active = pathname?.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-3 py-1.5 text-sm transition ${
                    active
                      ? "bg-white/[0.06] text-foreground"
                      : "text-foreground/60 hover:text-foreground"
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
        <ConnectButton />
      </div>
    </header>
  )
}
