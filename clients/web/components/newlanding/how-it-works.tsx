"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type Step = {
  title: string;
  label: string;
  description: string;
  image?: string;
};

const steps: Step[] = [
  {
    title: "Configure your agent.",
    label: "STEP 01",
    description:
      "Set your token pair, market type, LLM provider, risk limits, and any custom strategy overrides. Takes under two minutes — no boilerplate.",
  },
  {
    title: "Deploy anywhere.",
    label: "STEP 02",
    description:
      "Launch the agent locally or push it to a remote VM. The hub tracks heartbeats, persists state, and isolates every agent in its own process.",
    image: "/assets/robot_on.png",
  },
  {
    title: "Monitor & iterate.",
    label: "STEP 03",
    description:
      "Watch trades stream in real time. Agents auto-rebalance on schedule. Pause, reconfigure, or scale any agent with a single command.",
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto h-screen">
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
        className="text-xs tracking-[1.5px] uppercase text-gray mb-4"
      >
        How it works
      </motion.p>
      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
        className="text-[clamp(28px,4vw,44px)] font-bold tracking-tight text-white mb-14"
      >
        Configure. Deploy. Profit.
      </motion.h2>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
        className="rounded-3xl border border-white/10 bg-white/[0.02] backdrop-blur-sm overflow-hidden"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-white/10">
          {steps.map((step, i) => (
            <StepCard key={step.label} step={step} index={i} />
          ))}
        </div>
      </motion.div>
    </section>
  );
}

function StepCard({ step, index }: { step: Step; index: number }) {
  const hasImage = !!step.image;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: index * 0.12 }}
      className={cn(
        "relative flex flex-col p-8 md:p-10 min-h-[440px] md:min-h-[520px]",
        hasImage && "bg-black/20"
      )}
    >
      {/* Image (middle card) */}
      {hasImage && (
        <div className="absolute inset-0 -z-10">
          {/* <Image
            src={step.image!}
            alt=""
            fill
            className="object-cover object-center opacity-40"
          /> */}
          <div className="absolute inset-0 bg-[#151B21]"/> {/*bg-gradient-to-b from-black/30 via-black/40 to-black/70" */}
        </div>
      )}

      {/* Title — top */}
      <h3 className="text-[clamp(24px,2.6vw,34px)] font-semibold tracking-tight text-white leading-[1.15] max-w-[18ch]">
        {step.title}
      </h3>

      {/* Spacer pushes label/desc to bottom */}
      <div className="flex-1" />

      {/* Label */}
      <p className="text-[11px] tracking-[1.5px] uppercase text-white/50 font-semibold mb-3">
        {step.label}
      </p>

      {/* Description */}
      <p className="text-[14px] text-white/60 leading-relaxed max-w-[34ch]">
        {step.description}
      </p>
    </motion.div>
  );
}
