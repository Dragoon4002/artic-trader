"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Entry = {
  hash: string;
  kind: "DECISION" | "TRADE" | "HALT";
  symbol: string;
  detail: string;
  block: number;
  age: string;
};

const seed: Entry[] = [
  { hash: "0x9f3ae21c4b88…d1a2", kind: "DECISION", symbol: "BTC/USDT", detail: "supervisor approve · momentum-v3", block: 18420115, age: "12s" },
  { hash: "0x4c12bb87fe1a…77c3", kind: "TRADE", symbol: "ETH/USDT", detail: "open long 0.42 ETH @ 3,420.18", block: 18420112, age: "31s" },
  { hash: "0x77ad06bd29ea…0ef9", kind: "HALT", symbol: "SOL/USDT", detail: "max session loss reached · halt", block: 18420108, age: "1m" },
  { hash: "0x231ec55da714…ba48", kind: "DECISION", symbol: "AVAX/USDT", detail: "switch strategy · vol-target", block: 18420101, age: "2m" },
  { hash: "0xab76f0c33e92…2b90", kind: "TRADE", symbol: "BTC/USDT", detail: "close short 0.18 BTC · pnl +1.42%", block: 18420090, age: "3m" },
  { hash: "0x05de91478af2…f6ce", kind: "DECISION", symbol: "LINK/USDT", detail: "skip · low confidence", block: 18420077, age: "4m" },
];

const kindColor: Record<Entry["kind"], string> = {
  DECISION: "#8FB1E8",
  TRADE: "#6FCAA0",
  HALT: "#F0C561",
};

export function OnchainProof() {
  const [entries, setEntries] = useState(seed);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      setEntries((prev) => {
        const head = prev[0];
        return [
          {
            ...head,
            hash: "0x" + Math.random().toString(16).slice(2, 14) + "…" + Math.random().toString(16).slice(2, 6),
            block: head.block + 1 + Math.floor(Math.random() * 4),
            age: "0s",
          },
          ...prev.slice(0, -1),
        ];
      });
    }, 3500);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="relative px-6 md:px-12 py-28 md:py-36 max-w-7xl mx-auto">
      {/* faint chain-link background accent */}
      <div
        aria-hidden
        className="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 w-64 h-64 opacity-[0.025]"
        style={{
          backgroundImage: "radial-gradient(circle, #8FB1E8 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-12 lg:gap-20 items-start">
        <div>
          <p className="text-[10px] tracking-[2.5px] uppercase text-foreground/35 font-mono mb-4">
            §07 — On-chain proof
          </p>
          <h2 className="text-[clamp(36px,4.6vw,60px)] font-light tracking-tight text-foreground leading-[0.95] mb-6">
            Every decision.<br />
            <em className="not-italic font-serif text-foreground/80">Cryptographically receipted.</em>
          </h2>
          <p className="text-[14px] text-foreground/55 leading-relaxed max-w-md mb-8">
            Supervisor verdicts, strategy switches, and trade fills emit signed events to <strong className="text-foreground/80 font-normal">0G Chain</strong>. Full LLM reasoning + trade JSON sealed on <strong className="text-foreground/80 font-normal">0G Storage</strong>; only the root hash lands on-chain. Replay any decision, three months later.
          </p>
          <div className="flex flex-wrap gap-2 mb-8">
            {["DecisionLogger", "TradeLogger", "StrategyINFT"].map((c) => (
              <span
                key={c}
                className="text-[11px] font-mono px-3 py-1.5 rounded-full border border-foreground/15 text-foreground/70"
              >
                {c}.sol
              </span>
            ))}
          </div>
          {/* block counter */}
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-accent animate-pulse shrink-0" />
            <span className="font-mono text-[11px] text-foreground/35 tabular-nums">
              block #{entries[0].block.toLocaleString()} · 0G Mainnet (chainId 16661)
            </span>
          </div>
        </div>

        <div className="relative rounded-2xl border border-foreground/10 bg-foreground/1.5 overflow-hidden">
          {/* top bar — blue accent to distinguish from LivePnlFeed */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-foreground/10 bg-blue-accent/5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-accent animate-pulse" />
              <span className="text-[11px] font-mono uppercase tracking-wider text-blue-accent/70">
                audit-stream · live
              </span>
            </div>
            <span className="text-[11px] font-mono text-foreground/30">
              #{entries[0].block}
            </span>
          </div>

          {/* column header */}
          <div className="px-4 py-2 border-b border-foreground/5 flex items-center gap-4 font-mono text-[10px] text-foreground/20 uppercase tracking-wider">
            <span className="w-20 shrink-0">type</span>
            <span className="w-24 shrink-0">symbol</span>
            <span className="flex-1">detail</span>
            <span className="hidden md:inline w-32">tx hash</span>
            <span className="w-10 text-right shrink-0">age</span>
          </div>

          <div className="divide-y divide-white/5">
            {entries.slice(0, 6).map((e, i) => (
              <motion.div
                key={`${e.hash}-${i}`}
                initial={{ opacity: 0, y: -8, backgroundColor: "rgba(143,177,232,0.06)" }}
                animate={{ opacity: 1, y: 0, backgroundColor: "rgba(143,177,232,0)" }}
                transition={{ duration: 0.3 }}
                className="px-4 py-3 flex items-center gap-4 font-mono text-[12px] hover:bg-foreground/2"
              >
                <span
                  className="text-[10px] tracking-[1.5px] uppercase w-20 shrink-0"
                  style={{ color: kindColor[e.kind] }}
                >
                  {e.kind}
                </span>
                <span className="text-foreground/50 w-24 shrink-0">{e.symbol}</span>
                <span className="text-foreground/75 flex-1 truncate">{e.detail}</span>
                <span className="text-foreground/25 hidden md:inline w-32 truncate">{e.hash}</span>
                <span className="text-foreground/35 w-10 text-right shrink-0">{e.age}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
