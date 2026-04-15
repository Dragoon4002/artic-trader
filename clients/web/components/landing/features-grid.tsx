"use client";

import { FeatureCard } from "./feature-card";
import { motion } from "framer-motion";
import {
  Zap,
  Brain,
  BarChart3,
  ShieldCheck,
  Globe,
  Radio,
} from "lucide-react";

const features = [
  {
    icon: <Zap className="h-5 w-5" />,
    color: "orange",
    title: "Multi-agent orchestration",
    description:
      "Launch dozens of agents simultaneously — locally or on remote VMs. Each agent runs isolated with its own config, strategy, and position.",
    hoverBg: "group-hover:bg-orange/[0.12]",
    visualGradient: "from-orange/20 to-orange-light/10",
  },
  {
    icon: <Brain className="h-5 w-5" />,
    color: "teal",
    title: "LLM strategy engine",
    description:
      "Agents study historical market data and let your chosen LLM select or generate the optimal strategy. Re-evaluates on your schedule.",
    hoverBg: "group-hover:bg-teal/[0.12]",
    visualGradient: "from-teal/20 to-teal-light/10",
  },
  {
    icon: <BarChart3 className="h-5 w-5" />,
    color: "red",
    title: "30+ quant strategies",
    description:
      "Start immediately with momentum, mean reversion, volatility, volume, and statistical strategies — all battle-tested on live markets.",
    hoverBg: "group-hover:bg-red/[0.12]",
    visualGradient: "from-red/20 to-red-light/10",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    color: "blue",
    title: "Risk-first architecture",
    description:
      "Per-agent position limits, drawdown stops, and kill switches. The hub maintains authority — no agent can exceed its mandate.",
    hoverBg: "group-hover:bg-blue-accent/[0.12]",
    visualGradient: "from-blue-accent/20 to-blue-light/10",
  },
  {
    icon: <Globe className="h-5 w-5" />,
    color: "orange",
    title: "Multi-market support",
    description:
      "Trade spot and perpetuals on HashKey Global, stream prices from Pyth, and log decisions on-chain — all from one hub.",
    hoverBg: "group-hover:bg-orange/[0.12]",
    visualGradient: "from-orange/20 to-teal/10",
  },
  {
    icon: <Radio className="h-5 w-5" />,
    color: "teal",
    title: "Real-time monitoring",
    description:
      "Live P&L, position snapshots, trade logs, and LLM reasoning — streamed to your dashboard, Telegram bot, or CLI in real time.",
    hoverBg: "group-hover:bg-teal/[0.12]",
    visualGradient: "from-teal/20 to-orange/10",
  },
];

export function FeaturesGrid() {
  return (
    <section id="features" className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4"
      >
        Core features
      </motion.p>
      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-[clamp(28px,4vw,44px)] font-bold tracking-tight text-white mb-4"
      >
        Everything an AI trader needs.
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, delay: 0.1, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-[17px] text-white/50 max-w-[520px] leading-relaxed"
      >
        From strategy selection to live execution — Artic handles the full
        lifecycle of every agent.
      </motion.p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-14">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: i * 0.1, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <FeatureCard {...f} />
          </motion.div>
        ))}
      </div>
    </section>
  );
}
