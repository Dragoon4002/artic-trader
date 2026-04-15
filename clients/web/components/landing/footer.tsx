import Link from "next/link";
import { Logo } from "@/components/shared/logo";

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
      { label: "GitHub", href: "#" },
      { label: "Telegram", href: "#" },
      { label: "Twitter / X", href: "#" },
      { label: "Discord", href: "#" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-white/8">
      <div className="px-6 md:px-12 py-12 md:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10">
          {/* Logo column */}
          <div className="col-span-2 md:col-span-1">
            <Logo size="small" />
            <p className="text-[13px] text-white/30 mt-3 max-w-48 leading-relaxed">
              AI-powered multi-agent trading platform.
            </p>
          </div>

          {/* Link columns */}
          {columns.map((col) => (
            <div key={col.title}>
              <p className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-4">
                {col.title}
              </p>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-[13px] text-white/35 hover:text-white/75 transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/5 px-6 md:px-12 py-5 flex flex-wrap justify-between items-center gap-4">
        <p className="text-xs text-white/20">
          © 2025 Silone Labs. All rights reserved.
        </p>
        <p className="text-xs text-white/20">
          Built with Next.js
        </p>
      </div>
    </footer>
  );
}
