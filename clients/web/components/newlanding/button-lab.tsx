"use client";

import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = {
  name: string;
  note: string;
  className: string;
  inner?: React.ReactNode;
  outer?: string;
};

const variants: Variant[] = [
  {
    name: "01 — Pill, current",
    note: "current. dark slate, light border",
    className:
      "bg-cta hover:bg-cta-hover border border-cta-border text-white rounded-full px-6 h-11 text-[14px] font-semibold gap-2",
    inner: (
      <>
        Get early access <ArrowRight className="w-4 h-4" />
      </>
    ),
  },
  {
    name: "02 — Sharp slab",
    note: "no radius. bold weight. monospaced action",
    className:
      "bg-cta hover:bg-cta-hover border border-cta-border text-white rounded-none px-6 h-11 text-[13px] font-bold uppercase tracking-[0.12em] gap-2 font-mono",
    inner: (
      <>
        Get access <span className="opacity-60">→</span>
      </>
    ),
  },
  {
    name: "03 — Inset shadow",
    note: "embossed. subtle highlight + drop",
    className:
      "bg-cta hover:bg-cta-hover text-white rounded-xl px-6 h-11 text-[14px] font-semibold gap-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.15),inset_0_-1px_0_rgba(0,0,0,0.4),0_4px_12px_-2px_rgba(0,0,0,0.4)] border border-black/40",
    inner: <>Launch app</>,
  },
  {
    name: "04 — Ghost outline",
    note: "stroke only. fills on hover",
    className:
      "bg-transparent text-white border-2 border-cta-border hover:bg-cta hover:border-cta rounded-full px-6 h-11 text-[14px] font-semibold gap-2 transition-all",
    inner: (
      <>
        Get started <ArrowRight className="w-4 h-4" />
      </>
    ),
  },
  {
    name: "05 — Split icon",
    note: "icon block separates from label",
    className:
      "bg-cta hover:bg-cta-hover text-white rounded-full pl-6 pr-2 h-11 text-[14px] font-semibold gap-3 border border-cta-border",
    inner: (
      <>
        <span>Try Artic free</span>
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-white/15 border border-white/20">
          <ArrowUpRight className="w-3.5 h-3.5" />
        </span>
      </>
    ),
  },
  {
    name: "06 — Hover slide",
    note: "label slides, arrow fills the slot",
    className:
      "bg-cta hover:bg-cta-hover text-white rounded-full px-6 h-11 text-[14px] font-semibold border border-cta-border overflow-hidden relative group/btn",
    inner: (
      <span className="relative flex items-center gap-2">
        <span className="transition-transform duration-300 group-hover/btn:-translate-x-2">
          Get early access
        </span>
        <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover/btn:translate-x-1" />
      </span>
    ),
  },
  {
    name: "07 — Underline reveal",
    note: "minimal. underline animates in",
    className:
      "bg-transparent text-white px-2 h-11 text-[15px] font-semibold border-0 relative group/btn",
    inner: (
      <span className="relative inline-flex items-center gap-2">
        Get early access
        <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover/btn:translate-x-1" />
        <span className="absolute -bottom-1 left-0 right-0 h-px bg-cta-border origin-left scale-x-0 transition-transform duration-300 group-hover/btn:scale-x-100" />
      </span>
    ),
  },
  {
    name: "08 — Wrapped frame",
    note: "outer chrome ring around solid button",
    className:
      "bg-cta hover:bg-cta-hover text-white rounded-full px-6 h-10 text-[14px] font-semibold gap-2 border border-cta-border",
    inner: (
      <>
        Get early access <ArrowRight className="w-4 h-4" />
      </>
    ),
    outer: "p-1 rounded-full bg-white/5 border border-white/10",
  },
  {
    name: "09 — Soft tactile",
    note: "rounded-2xl. gentle gradient. warm",
    className:
      "rounded-2xl px-6 h-11 text-[14px] font-semibold text-white gap-2 border border-cta-border bg-gradient-to-b from-[#3d4c58] to-cta hover:from-cta hover:to-cta-hover transition-colors",
    inner: (
      <>
        Get early access <ArrowRight className="w-4 h-4" />
      </>
    ),
  },
];

function VariantTile({ v }: { v: Variant }) {
  const btn = (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center transition-colors cursor-pointer",
        v.className
      )}
    >
      {v.inner}
    </button>
  );

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 flex flex-col gap-5">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-xs font-mono uppercase tracking-wider text-white/50">
          {v.name}
        </p>
      </div>
      <div className="flex-1 flex items-center justify-center min-h-[80px]">
        {v.outer ? <span className={v.outer}>{btn}</span> : btn}
      </div>
      <p className="text-xs text-white/40 leading-relaxed">{v.note}</p>
    </div>
  );
}

export function ButtonLab() {
  return (
    <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto">
      <p className="text-xs tracking-[1.5px] uppercase text-accent-gray mb-4">
        Button lab
      </p>
      <h2 className="text-[clamp(28px,4vw,44px)] font-bold tracking-tight text-white mb-3">
        Pick a primary you actually like.
      </h2>
      <p className="text-[15px] text-white/50 max-w-xl leading-relaxed mb-12">
        Same color tokens, different gestures. Hover each to feel it.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {variants.map((v) => (
          <VariantTile key={v.name} v={v} />
        ))}
      </div>

      <p className="text-xs text-white/30 mt-10">
        Tell me a number and I'll wire it as the production primary across hero,
        navbar, and CTA banner.
      </p>

      {/* Suppress unused-import warning until wired up */}
      <Link href="#" className="hidden">
        _
      </Link>
    </section>
  );
}
