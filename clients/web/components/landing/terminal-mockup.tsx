"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Line = {
  prefix?: string;
  text: string;
  color?: string;
  delay: number;
};

const lines: Line[] = [
  { prefix: "$ ", text: "uvicorn hub.server:app --port 8000", color: "text-orange-light", delay: 0 },
  { text: "✓ Hub online — 4 agents registered", color: "text-teal", delay: 0.6 },
  { prefix: "", text: "", delay: 0.9 },
  { prefix: "$ ", text: "curl -X POST /api/agents -d '{\"symbol\": \"BTC/USDT\", \"strategy\": \"momentum\"}'", color: "text-orange-light", delay: 1.2 },
  { text: "→ Agent btc-001 created (port 8101)", color: "text-white/60", delay: 1.8 },
  { prefix: "", text: "", delay: 2.0 },
  { prefix: "$ ", text: "curl -X POST /api/agents/btc-001/start", color: "text-orange-light", delay: 2.3 },
  { text: "✓ Spawning container… analyzing 72h market data", color: "text-teal", delay: 2.9 },
  { text: "✓ AI planner selected: momentum_breakout_v2 (confidence 87%)", color: "text-teal", delay: 3.4 },
  { text: "✓ Agent live on HashKey Global perp — size $2,400", color: "text-teal", delay: 3.9 },
  { prefix: "", text: "", delay: 4.1 },
  { prefix: "$ ", text: "curl /api/agents/btc-001/status", color: "text-orange-light", delay: 4.4 },
  { text: "{", color: "text-white/40", delay: 4.8 },
  { text: '  "pnl": "+$184.20",  "win_rate": "68%",  "trades": 23,', color: "text-orange-text", delay: 5.0 },
  { text: '  "position": "LONG 0.04 BTC",  "uptime": "6h 14m"', color: "text-orange-text", delay: 5.2 },
  { text: "}", color: "text-white/40", delay: 5.4 },
  { prefix: "", text: "", delay: 5.6 },
  { text: "  streaming to dashboard / telegram / cli ▊", color: "text-white/25", delay: 5.9 },
];

export function TerminalMockup() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    if (visibleCount >= lines.length) return;
    const next = lines[visibleCount];
    const timer = setTimeout(
      () => setVisibleCount((c) => c + 1),
      visibleCount === 0 ? 400 : (next.delay - (lines[visibleCount - 1]?.delay ?? 0)) * 1000
    );
    return () => clearTimeout(timer);
  }, [visibleCount]);

  return (
    <div className="relative z-10 mt-16 w-full max-w-[900px] mx-auto border border-white/10 rounded-2xl overflow-hidden bg-white/[0.03]">
      {/* Title bar */}
      <div className="flex items-center gap-1.5 px-4 py-2.5 bg-white/[0.05] border-b border-white/[0.08]">
        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <span className="text-xs text-white/30 ml-2">artic-hub — terminal</span>
      </div>

      {/* Body */}
      <div className="p-6 md:p-7 font-mono text-[13px] leading-[1.9] text-white/70 min-h-[320px]">
        {lines.slice(0, visibleCount).map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className={line.text === "" ? "h-3" : undefined}
          >
            {line.text && (
              <>
                {line.prefix !== undefined ? (
                  <>
                    <span className="text-white/35">{line.prefix}</span>
                    <span className={line.color ?? "text-white/70"}>{line.text}</span>
                  </>
                ) : (
                  <span className={line.color ?? "text-white/70"}>
                    {line.text.startsWith("✓") && <span className="text-teal">✓</span>}
                    {line.text.startsWith("✓") ? line.text.slice(1) : line.text}
                  </span>
                )}
              </>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
