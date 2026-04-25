"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap,
  Brain,
  BarChart3,
  ShieldCheck,
  Globe,
  Radio,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    icon: Brain,
    color: "teal",
    title: "LLM strategy engine",
    short: "AI picks the strategy",
    description:
      "Agents study historical market data and let your chosen LLM select or generate the optimal strategy. Re-evaluates on your schedule.",
    accent: ["#135c46", "#2a8a6a"] as [string, string],
  },
  {
    icon: Zap,
    color: "orange",
    title: "Multi-agent orchestration",
    short: "Run dozens in parallel",
    description:
      "Launch dozens of agents simultaneously — locally or on remote VMs. Each agent runs isolated with its own config, strategy, and position.",
    accent: ["#7a3318", "#a0522d"] as [string, string],
  },
  {
    icon: BarChart3,
    color: "red",
    title: "30+ quant strategies",
    short: "Battle-tested on live markets",
    description:
      "Start immediately with momentum, mean reversion, volatility, volume, and statistical strategies — all proven on live markets.",
    accent: ["#7a1818", "#b03030"] as [string, string],
  },
  {
    icon: ShieldCheck,
    color: "blue",
    title: "Risk-first architecture",
    short: "Hub keeps the kill switch",
    description:
      "Per-agent position limits, drawdown stops, and kill switches. The hub maintains authority — no agent can exceed its mandate.",
    accent: ["#1e4f7a", "#3a7ab8"] as [string, string],
  },
  {
    icon: Globe,
    color: "orange",
    title: "Multi-market support",
    short: "Spot, perps, on-chain",
    description:
      "Trade spot and perpetuals on HashKey Global, stream prices from Pyth, and log decisions on-chain — all from one hub.",
    accent: ["#7a3318", "#1e4f7a"] as [string, string],
  },
  {
    icon: Radio,
    color: "teal",
    title: "Real-time monitoring",
    short: "Live PnL, logs, reasoning",
    description:
      "Live P&L, position snapshots, trade logs, and LLM reasoning — streamed to your dashboard, Telegram bot, or CLI in real time.",
    accent: ["#135c46", "#7a3318"] as [string, string],
  },
];

const springBouncy = { type: "spring" as const, stiffness: 350, damping: 22, mass: 0.7 };

function IconPanel({ idx }: { idx: number }) {
  const f = features[idx];
  const Icon = f.icon;
  return (
    <motion.div
      key={idx}
      className="w-full aspect-square rounded-3xl overflow-hidden relative border border-white/10"
      style={{ background: f.accent[0] }}
      initial={{ opacity: 0, scale: 0.92, rotate: -2 }}
      animate={{ opacity: 1, scale: 1, rotate: 0 }}
      exit={{ opacity: 0, scale: 0.92, rotate: 2 }}
      transition={springBouncy}
    >
      <motion.div
        className="absolute rounded-full"
        style={{ width: "70%", height: "70%", background: f.accent[1], right: "-12%", bottom: "-12%" }}
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 0.7 }}
        transition={{ ...springBouncy, delay: 0.05 }}
      />
      <motion.div
        className="absolute rounded-full"
        style={{ width: "45%", height: "45%", background: `${f.accent[1]}cc`, right: "8%", bottom: "8%" }}
        initial={{ scale: 0.3, opacity: 0 }}
        animate={{ scale: 1, opacity: 0.6 }}
        transition={{ ...springBouncy, delay: 0.1 }}
      />
      <motion.div
        className="absolute"
        style={{
          width: "40%",
          height: "100%",
          background: `linear-gradient(180deg, ${f.accent[0]}88, ${f.accent[1]}33)`,
          left: "28%",
          top: 0,
        }}
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 0.5, x: 0 }}
        transition={{ ...springBouncy, delay: 0.08 }}
      />
      {/* Centered icon */}
      <motion.div
        className="absolute inset-0 flex items-center justify-center text-white/95 drop-shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ ...springBouncy, delay: 0.12 }}
      >
        <Icon className="w-24 h-24 md:w-28 md:h-28" strokeWidth={1.4} />
      </motion.div>
    </motion.div>
  );
}

export function FeaturesGrid() {
  const [active, setActive] = useState(0);
  const activeFeature = features[active];

  return (
    <section
      id="features"
      className="py-24 px-6 md:px-12 max-w-7xl mx-auto h-screen"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-start">
        {/* Left: heading + feature list */}
        <div className="flex flex-col justify-between h-full">
          <div>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="text-xs tracking-[1.5px] uppercase text-gray mb-4"
            >
              Core features
            </motion.p>
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="text-[clamp(40px,6vw,72px)] font-bold tracking-tighter text-white mt-10 mb-4 leading-[1]"
            >
              Features
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="text-xs tracking-[1.5px] uppercase text-white/70"
            >
              Explore what we can offer you
            </motion.p>
          </div>

          <div className="border-t border-white/10">
            {features.map((f, i) => {
              const isActive = i === active;
              return (
                <button
                  key={f.title}
                  type="button"
                  onMouseEnter={() => setActive(i)}
                  onFocus={() => setActive(i)}
                  onClick={() => setActive(i)}
                  className={cn(
                    "group relative w-full flex items-center justify-between py-5 px-4 border-b border-white/10 text-left transition-colors duration-200",
                    isActive ? "bg-white/[0.04]" : "hover:bg-white/[0.02]"
                  )}
                >
                  {/* Active indicator bar */}
                  {isActive && (
                    <motion.span
                      layoutId="feature-active-bar"
                      className="absolute left-0 top-0 bottom-0 w-[2px] bg-orange"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span
                    className={cn(
                      "text-[17px] font-medium transition-colors",
                      isActive ? "text-white" : "text-white/70 group-hover:text-white"
                    )}
                  >
                    {f.title}
                  </span>
                  <span
                    className={cn(
                      "transition-colors duration-300",
                      isActive ? "text-gray" : "text-white/40 group-hover:text-white/70"
                    )}
                  >
                    <ArrowRight
                      className={cn(
                        "w-5 h-5 transition-transform duration-300 ease-out",
                        isActive ? "-rotate-45" : "rotate-0"
                      )}
                    />
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: detail panel */}
        <div className="lg:sticky lg:top-28">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
              className="mb-8"
            >
              <p className="text-xs tracking-[1.5px] uppercase text-white/40 mb-3">
                {`0${active + 1}`.slice(-2)} — {activeFeature.short}
              </p>
              <h3 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4 leading-tight">
                {activeFeature.title}
              </h3>
              <p className="text-[15px] text-white/55 leading-relaxed max-w-lg">
                {activeFeature.description}
              </p>
            </motion.div>
          </AnimatePresence>

          <div className="relative max-w-lg">
            <AnimatePresence mode="wait">
              <IconPanel idx={active} />
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
