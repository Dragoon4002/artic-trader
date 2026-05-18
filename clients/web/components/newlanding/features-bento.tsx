"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { useRef, useState } from "react";

const features = [
  {
    title: "TEE-sealed LLM engine",
    tag: "0G Compute",
    description:
      "Planner + supervisor LLMs run inside TeeML on 0G Compute. Provider signs every response; hash folds into the on-chain reasoning record.",
    icon: "/assets/landing/icons/fox-brain.svg",
    accent: "#6FCAA0",
    pills: ["0G Compute", "TeeML", "Sealed infer"],
  },
  {
    title: "Multi-agent orchestration",
    tag: "Agents",
    description:
      "One isolated process per symbol. Each with its own config, position, and LLM context.",
    icon: "/assets/landing/icons/paw-pack.svg",
    accent: "#F3E4D1",
    pills: ["Per-symbol", "Isolated VM", "Parallel"],
  },
  {
    title: "30+ quant strategies",
    tag: "Algorithms",
    description:
      "Momentum, mean-rev, stat-arb, vol, smart-money, RWA — all proven on live markets.",
    icon: "/assets/landing/icons/glacier-chart.svg",
    accent: "#8FB1E8",
    pills: ["Momentum", "Mean-rev", "Stat-arb"],
  },
  {
    title: "Risk-first architecture",
    tag: "Safety",
    description:
      "Per-agent drawdown caps and kill switches. Hub authority — no agent exceeds its mandate.",
    icon: "/assets/landing/icons/ice-shield.svg",
    accent: "#B3C9EE",
    pills: ["Kill switch", "Drawdown cap", "Hub auth"],
  },
  {
    title: "Verifiable on-chain audit",
    tag: "0G Chain",
    description:
      "DecisionLogger + TradeLogger emit indexed events for every supervisor verdict and fill on 0G Mainnet. Reasoning + trade JSON sealed on 0G Storage, bound by hash.",
    icon: "/assets/landing/icons/frozen-globe.svg",
    accent: "#6FCAA0",
    pills: ["0G Chain", "0G Storage", "TradeLogger"],
  },
  {
    title: "Tradable strategy INFTs",
    tag: "ERC-7857",
    description:
      "Every published strategy mints an Agent ID (ERC-7857 INFT). Encrypted config, sealed-executor usage rights, re-encryption on transfer — buyers run it without ever seeing it.",
    icon: "/assets/landing/icons/aurora-pulse.svg",
    accent: "#F0C561",
    pills: ["ERC-7857", "INFT", "Sealed config"],
  },
];

const COL_TPLS = ["2fr 0.75fr 0.75fr", "0.75fr 2fr 0.75fr", "0.75fr 0.75fr 2fr"];
const ROW_TPLS = ["2fr 0.75fr", "0.75fr 2fr"];
const BASE_COLS = "1fr 1fr 1fr";
const BASE_ROWS = "1fr 1fr";

export function FeaturesBento() {
  const [active, setActive] = useState<number | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  function setGrid(col: number | null, row: number | null) {
    const el = gridRef.current;
    if (!el) return;
    el.style.gridTemplateColumns = col !== null ? COL_TPLS[col] : BASE_COLS;
    el.style.gridTemplateRows    = row !== null ? ROW_TPLS[row] : BASE_ROWS;
  }

  function enter(i: number) {
    if (timer.current) clearTimeout(timer.current);
    setActive(i);
    setGrid(i % 3, Math.floor(i / 3));
  }

  function leave() {
    timer.current = setTimeout(() => {
      setActive(null);
      setGrid(null, null);
    }, 80);
  }

  return (
    <section className="px-6 md:px-12 py-24 md:py-36 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.5 }}
        className="mb-12"
      >
        <p className="text-[10px] tracking-[2.5px] uppercase text-foreground/35 font-mono mb-3">
          Capabilities
        </p>
        <h2 className="text-[clamp(36px,5vw,64px)] font-light tracking-tight text-foreground leading-[0.95]">
          Everything your pack needs.
        </h2>
      </motion.div>

      <div
        ref={gridRef}
        style={{
          display: "grid",
          gridTemplateColumns: BASE_COLS,
          gridTemplateRows: BASE_ROWS,
          gap: "10px",
          height: "490px",
          transition:
            "grid-template-columns 0.55s cubic-bezier(0.4,0,0.2,1), grid-template-rows 0.55s cubic-bezier(0.4,0,0.2,1)",
        }}
      >
        {features.map((f, i) => (
          <BentoCell
            key={f.title}
            feature={f}
            isActive={active === i}
            onEnter={() => enter(i)}
            onLeave={leave}
          />
        ))}
      </div>
    </section>
  );
}

function BentoCell({
  feature: f,
  isActive,
  onEnter,
  onLeave,
}: {
  feature: (typeof features)[0];
  isActive: boolean;
  onEnter: () => void;
  onLeave: () => void;
}) {
  return (
    <div
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      style={{
        borderRadius: "16px",
        border: `1px solid ${isActive ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.08)"}`,
        background: "#0A0E12",
        overflow: "hidden",
        cursor: "default",
        position: "relative",
        transition: "border-color 0.3s ease",
      }}
    >
      {/* accent bg */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(70% 60% at 90% 10%, ${f.accent}, transparent)`,
          opacity: isActive ? 0.14 : 0.07,
          transition: "opacity 0.4s ease",
        }}
      />

      {/* content */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          padding: "1.25rem 1.4rem",
          height: "100%",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* top row: tag + icon */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "10px" }}>
          <span
            style={{
              fontSize: "10px",
              fontWeight: 500,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              padding: "3px 9px",
              borderRadius: "20px",
              background: `${f.accent}1a`,
              color: f.accent,
              border: `0.5px solid ${f.accent}33`,
              fontFamily: "var(--font-mono, monospace)",
              whiteSpace: "nowrap",
            }}
          >
            {f.tag}
          </span>
          <div
            style={{
              width: isActive ? 44 : 34,
              height: isActive ? 44 : 34,
              position: "relative",
              flexShrink: 0,
              transition: "width 0.55s cubic-bezier(0.4,0,0.2,1), height 0.55s cubic-bezier(0.4,0,0.2,1)",
            }}
          >
            <Image src={f.icon} alt={f.title} fill className="object-contain" />
          </div>
        </div>

        {/* title */}
        <p
          style={{
            fontSize: isActive ? "20px" : "15px",
            fontWeight: 300,
            color: "rgba(242,240,235,1)",
            margin: "0 0 6px",
            lineHeight: 1.25,
            letterSpacing: "-0.02em",
            transition: "font-size 0.55s cubic-bezier(0.4,0,0.2,1)",
          }}
        >
          {f.title}
        </p>

        {/* description */}
        <p
          style={{
            fontSize: "13px",
            color: "rgba(242,240,235,0.5)",
            lineHeight: 1.6,
            margin: 0,
            opacity: isActive ? 1 : 0,
            maxHeight: isActive ? "120px" : "0px",
            overflow: "hidden",
            transition: "opacity 0.35s ease 0.12s, max-height 0.5s cubic-bezier(0.4,0,0.2,1) 0.05s",
          }}
        >
          {f.description}
        </p>

        {/* pills */}
        <div
          style={{
            display: "flex",
            gap: "6px",
            flexWrap: "wrap",
            marginTop: "auto",
            paddingTop: "10px",
            opacity: isActive ? 1 : 0,
            maxHeight: isActive ? "60px" : "0px",
            overflow: "hidden",
            transition: "opacity 0.3s ease 0.2s, max-height 0.5s cubic-bezier(0.4,0,0.2,1) 0.05s",
          }}
        >
          {f.pills.map((p) => (
            <span
              key={p}
              style={{
                fontSize: "11px",
                padding: "3px 10px",
                borderRadius: "20px",
                border: "0.5px solid rgba(255,255,255,0.15)",
                color: "rgba(255,255,255,0.55)",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {p}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
