"use client";

import Link from "next/link";
import { useState } from "react";
import { GitBranch, X, MessageCircle } from "lucide-react";

const INK = "#0E141A";

const resources = [
  { label: "Agent Framework", href: "/docs" },
  { label: "Strategy Catalog", href: "/docs/strategies" },
  { label: "Hub API", href: "/docs/hub-api" },
  { label: "Smart Contracts", href: "/docs/architecture" },
];

const socials = [
  { label: "Twitter / X", href: "https://x.com/artic_trade", Icon: X },
  { label: "GitHub", href: "https://github.com/Dragoon4002/artic-trader", Icon: GitBranch },
];

export function Footer() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setSent(true);
  }

  return (
    <footer className="relative overflow-hidden" style={{ background: "#CCD2D6" }}>
      {/* 3-col grid */}
      <div
        className="grid grid-cols-1 md:grid-cols-3"
        style={{ borderColor: `${INK}20` }}
      >
        {/* col 1 — resources */}
        <div
          className="px-8 md:px-12 pt-10 pb-12 md:border-r"
          style={{ borderColor: `${INK}20` }}
        >
          <p
            className="text-[10px] tracking-[2.5px] uppercase font-mono mb-6"
            style={{ color: `${INK}55` }}
          >
            Resources (coming soon)
          </p>
          <ul className="space-y-3">
            {resources.map(({ label, href }) => (
              <li key={label}>
                <Link
                  href={href}
                  className="text-[14px] transition-opacity hover:opacity-100"
                  style={{ color: `${INK}99` }}
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* col 2 — socials */}
        <div
          className="px-8 md:px-12 pt-10 pb-12 md:border-r"
          style={{ borderColor: `${INK}20` }}
        >
          <p
            className="text-[10px] tracking-[2.5px] uppercase font-mono mb-6"
            style={{ color: `${INK}55` }}
          >
            Socials
          </p>
          <ul className="space-y-3">
            {socials.map(({ label, href, Icon }) => (
              <li key={label}>
                <Link
                  href={href}
                  className="flex items-center gap-3 text-[14px] transition-opacity hover:opacity-100"
                  style={{ color: `${INK}99` }}
                >
                  {Icon && <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: `${INK}55` }} />}
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* col 3 — waitlist */}
        <div className="px-8 md:px-12 pt-10 pb-12 flex flex-col justify-between gap-8">
          <div>
            <p
              className="text-[10px] tracking-[2.5px] uppercase font-mono mb-5"
              style={{ color: `${INK}55` }}
            >
              Waitlist
            </p>
            <h2
              className="font-serif text-[clamp(22px,2.4vw,32px)] font-light leading-[1.1] mb-2"
              style={{ color: INK }}
            >
              Be first on<br />the rate curve.
            </h2>
            <p className="text-[12px] mb-5 leading-relaxed" style={{ color: `${INK}80` }}>
              Early access to the platform, strategy updates, and launch news.
            </p>

            {sent ? (
              <p className="text-[13px] font-mono" style={{ color: INK }}>↳ You&apos;re on the list.</p>
            ) : (
              <form
                onSubmit={handleSubmit}
                className="flex items-center border-b transition-colors"
                style={{ borderColor: `${INK}30` }}
              >
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@domain.com"
                  className="flex-1 bg-transparent text-[13px] py-2.5 outline-none font-mono"
                  style={{ color: INK }}
                />
                <button
                  type="submit"
                  aria-label="Join waitlist"
                  className="pl-3 text-[16px] transition-opacity hover:opacity-100"
                  style={{ color: `${INK}55` }}
                >
                  ↗
                </button>
              </form>
            )}
          </div>

          <p className="text-[11px] font-mono" style={{ color: `${INK}50` }}>
            © 2026 Silone Labs
          </p>
        </div>
      </div>

      {/* dot divider */}
      {/* <div
        className="flex justify-center py-3 border-t"
        style={{ borderColor: `${INK}15` }}
      >
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#A0623A" }} />
      </div> */}

      {/* giant wordmark */}
      <div className="overflow-hidden leading-none select-none pointer-events-none" aria-hidden>
        <p
          className="font-serif font-bold tracking-tighter text-center whitespace-nowrap"
          style={{
            fontSize: "clamp(80px, 18vw, 260px)",
            lineHeight: 0.82,
            marginBottom: "-0.12em",
            color: `${INK}18`,
          }}
        >
          ARTIC
        </p>
      </div>
    </footer>
  );
}
