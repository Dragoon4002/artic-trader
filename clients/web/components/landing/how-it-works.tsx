"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// --- Data ---

const steps = [
  {
    num: 1,
    title: "Configure your agent",
    description:
      "Set your token pair, market type, LLM provider, risk limits, and any custom strategy overrides. Takes under two minutes.",
  },
  {
    num: 2,
    title: "Deploy anywhere",
    description:
      "Launch the agent locally or push it to a remote VM. Artic hub tracks it, maintains heartbeats, and persists all state to the DB.",
  },
  {
    num: 3,
    title: "Monitor & iterate",
    description:
      "Watch trades in real time. Agents auto-rebalance on your schedule. Pause, reconfigure, or scale any agent with a single command.",
  },
];

const springBouncy = { type: "spring" as const, stiffness: 350, damping: 20, mass: 0.7 };

// --- Mockup panels ---

function ConfigMockup() {
  return (
    <div className="font-mono text-[13px] leading-[1.8] p-5">
      <p className="text-white/30 mb-3"># agent.yaml</p>
      <p><span className="text-orange-light">name</span><span className="text-white/30">:</span> <span className="text-teal-light">BTC Long Momentum</span></p>
      <p><span className="text-orange-light">symbol</span><span className="text-white/30">:</span> <span className="text-teal-light">BTCUSDT</span></p>
      <p><span className="text-orange-light">amount_usdt</span><span className="text-white/30">:</span> <span className="text-red-light">100.0</span></p>
      <p><span className="text-orange-light">leverage</span><span className="text-white/30">:</span> <span className="text-red-light">5</span></p>
      <p><span className="text-orange-light">risk_profile</span><span className="text-white/30">:</span> <span className="text-teal-light">moderate</span></p>
      <p><span className="text-orange-light">timeframe</span><span className="text-white/30">:</span> <span className="text-teal-light">15m</span></p>
      <p><span className="text-orange-light">tp_pct</span><span className="text-white/30">:</span> <span className="text-red-light">0.05</span>  <span className="text-white/20">|</span>  <span className="text-orange-light">sl_pct</span><span className="text-white/30">:</span> <span className="text-red-light">0.02</span></p>
      <p><span className="text-orange-light">llm</span><span className="text-white/30">:</span> <span className="text-teal-light">anthropic / claude-3-5-sonnet</span></p>
    </div>
  );
}

function DeployMockup() {
  return (
    <div className="font-mono text-[13px] leading-[1.9] p-5">
      <p><span className="text-white/30">$ </span><span className="text-orange-light">POST /api/agents/btc-001/start</span></p>
      <p className="text-white/50"><span className="text-blue-light">[INIT]</span> Starting session for BTCUSDT</p>
      <p className="text-white/50"><span className="text-blue-light">[INIT]</span> Position: 100 USDT, Leverage: 5x</p>
      <p className="text-white/50"><span className="text-orange-text">[LLM]</span>  Strategy: momentum (confidence 87%)</p>
      <p className="text-white/50"><span className="text-teal">[START]</span> Trading loop active (poll 1.0s)</p>
      <p><span className="text-teal">✓</span> <span className="text-white/60">Agent alive on port 8432</span></p>
    </div>
  );
}

function MonitorMockup() {
  return (
    <div className="font-mono text-[13px] leading-[1.7] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-white font-semibold text-sm">BTC Long Momentum</span>
        <span className="flex items-center gap-1.5 text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
          <span className="text-teal-light">LIVE</span>
        </span>
      </div>
      <div className="h-px bg-white/10 mb-3" />
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-white/40">PnL</span>
          <span className="text-teal-light">+$512.25 <span className="text-white/30">▲ 5.12%</span></span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/40">Win Rate</span>
          <span className="text-white/70">63.8% <span className="text-white/30">· 47 trades</span></span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/40">Position</span>
          <span className="text-orange-text">LONG 0.04 BTC</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/40">Strategy</span>
          <span className="text-white/70">momentum</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/40">Sharpe</span>
          <span className="text-white/70">1.85</span>
        </div>
      </div>
    </div>
  );
}

const mockups = [ConfigMockup, DeployMockup, MonitorMockup];

// --- Mockup shell wrapper ---

function MockupShell({ stepIdx }: { stepIdx: number }) {
  const titles = ["agent.yaml", "terminal — deploy", "dashboard — btc-001"];
  const Mockup = mockups[stepIdx];
  return (
    <motion.div
      key={stepIdx}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={springBouncy}
      className="border border-white/10 rounded-2xl overflow-hidden bg-white/[0.03]"
    >
      <div className="flex items-center gap-1.5 px-4 py-2.5 bg-white/[0.05] border-b border-white/[0.08]">
        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <span className="text-xs text-white/30 ml-2">{titles[stepIdx]}</span>
      </div>
      <Mockup />
    </motion.div>
  );
}

// --- Main component ---

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];

    stepRefs.current.forEach((el, i) => {
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActiveStep(i);
        },
        { threshold: 0.6 }
      );
      obs.observe(el);
      observers.push(obs);
    });

    return () => observers.forEach((o) => o.disconnect());
  }, []);

  return (
    <section className="pb-24 px-6 md:px-12 max-w-[1200px] mx-auto">
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4"
      >
        How it works
      </motion.p>
      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-[clamp(28px,4vw,44px)] font-bold tracking-tight text-white mb-4"
      >
        Configure. Deploy. Profit.
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, delay: 0.1, ease: [0.25, 0.1, 0.25, 1] }}
        className="text-[17px] text-white/50 max-w-[520px] leading-relaxed"
      >
        Three steps from intent to live trading agent.
      </motion.p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 mt-14">
        {/* Left: step cards */}
        <div className="space-y-0">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              ref={(el) => { stepRefs.current[i] = el; }}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: [0.25, 0.1, 0.25, 1] }}
              className="min-h-[90vh] p-8"
            >
              <div className="sticky top-1/2 -translate-y-1/2">
                <div className={cn(
                  "w-7 h-7 rounded-full text-xs font-semibold flex items-center justify-center mb-5 transition-colors duration-300",
                  activeStep === i ? "bg-orange/30 text-orange-light" : "bg-orange/15 text-orange"
                )}>
                  {step.num}
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  {step.title}
                </h3>
                <p className="text-[15px] text-white/50 leading-relaxed max-w-md">
                  {step.description}
                </p>
              </div>

              {/* Mobile inline mockup */}
              <div className="mt-6 lg:hidden">
                <MockupShell stepIdx={i} />
              </div>
            </motion.div>
          ))}
        </div>

        {/* Right: sticky panel (desktop only) */}
        <div className="hidden lg:block">
          <div className="sticky top-24 h-[calc(90vh-6rem)] flex items-center">
            <div className="w-full">
              <AnimatePresence mode="wait">
                <MockupShell stepIdx={activeStep} />
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
