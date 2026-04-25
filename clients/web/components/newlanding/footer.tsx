import Link from "next/link";
import { GitBranch, Send, X, MessagesSquare } from "lucide-react";
import { Logo } from "@/components/shared/logo";

const INK = "#0E141A";

const columns = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "/#features" },
      { label: "Quickstart", href: "/docs/quickstart" },
      { label: "Strategy Catalog", href: "/docs/strategies" },
      { label: "API Reference", href: "/docs/hub-api" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "/docs" },
      { label: "Litepaper", href: "/litepaper" },
      { label: "Architecture", href: "/docs/architecture" },
      { label: "Blog", href: "/blog" },
      { label: "Jobs", href: "/jobs" },
    ],
  },
  {
    title: "Community",
    links: [
      { label: "Github", href: "https://github.com/Dragoon4002/Artic_trader" },
      { label: "Telegram", href: "#" },
      { label: "Twitter / X", href: "#" },
      { label: "Discord", href: "#" },
    ],
  },
];

const socials = [
  { icon: GitBranch, href: "https://github.com/Dragoon4002/Artic_trader", label: "GitHub" },
  { icon: X, href: "#", label: "Twitter" },
  { icon: Send, href: "#", label: "Telegram" },
  { icon: MessagesSquare, href: "#", label: "Discord" },
];

export function Footer() {
  return (
    <footer
      className="relative overflow-hidden bg-[#CCD2D6]"
      style={{ color: INK }}
    >
      <div className="relative px-6 md:px-12 mb-8">
        {/* Wordmark / tagline */}
        <div className="max-w-7xl mx-auto mb-8 md:mb-24">
          <h2
            className="text-[clamp(40px,6vw,72px)] font-bold tracking-tighter leading-[1.05] bg-clip-text text-transparent"
            style={{
              backgroundImage: `linear-gradient(180deg, rgba(14,20,26,0.45) 0%, ${INK} 100%)`,
            }}
          >
            Let your Pack Trade for You.
          </h2>
          <p className="mt-4 text-[18px] leading-relaxed max-w-7xl" style={{ color: `${INK}99` }}>
            Multi-agent AI traders, on-chain transparency, and 30+ quant
            strategies — all coordinated by one hub.
          </p>
        </div>

        {/* Link grid */}
        <div
          className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-5 gap-10 pb-12 border-b"
          style={{ borderColor: `${INK}1f` }}
        >
          <div className="col-span-2 md:col-span-2">
            <Logo size="small" />
            <p className="text-[13px] mt-3 max-w-xs leading-relaxed" style={{ color: `${INK}99` }}>
              AI-powered multi-agent trading platform built on Initia.
            </p>

            {/* Status pill */}
            <div
              className="mt-5 inline-flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-sm"
              style={{
                background: `${INK}0d`,
                border: `1px solid ${INK}1f`,
              }}
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-75 animate-ping" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-teal" />
              </span>
              <span className="text-xs" style={{ color: INK }}>All systems operational</span>
            </div>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <p
                className="text-xs font-semibold uppercase tracking-wider mb-4"
                style={{ color: INK }}
              >
                {col.title}
              </p>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-[13px] transition-colors hover:opacity-100"
                      style={{ color: `${INK}b3` }}
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="max-w-7xl mx-auto pt-6 flex flex-wrap justify-between items-center gap-4">
          <p className="text-xs" style={{ color: `${INK}80` }}>
            © 2026 Silone Labs. All rights reserved.
          </p>

          <div className="flex items-center gap-2">
            {socials.map(({ icon: Icon, href, label }) => (
              <Link
                key={label}
                href={href}
                aria-label={label}
                className="w-8 h-8 flex items-center justify-center rounded-full transition-colors"
                style={{
                  background: `${INK}0d`,
                  border: `1px solid ${INK}1f`,
                  color: `${INK}b3`,
                }}
              >
                <Icon className="w-3.5 h-3.5" />
              </Link>
            ))}
          </div>

          <p className="text-xs" style={{ color: `${INK}80` }}>
            Built on Initia · Powered by Morph VM
          </p>
        </div>
      </div>
    </footer>
  );
}
