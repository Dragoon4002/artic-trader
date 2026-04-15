import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { TerminalMockup } from "./terminal-mockup";
import { cn } from "@/lib/utils";

export function Hero() {
  return (
    <section className="relative min-h-[88vh] flex flex-col items-center justify-center text-center px-6 py-40 overflow-hidden">
      {/* Gradient background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: `
            radial-gradient(ellipse 60% 50% at 50% 0%, rgba(218,119,86,0.25) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 20% 80%, rgba(29,158,117,0.12) 0%, transparent 60%),
            #0a0a0f
          `,
        }}
      />

      {/* Badge */}
      <div className="relative z-10 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-orange-light/50 bg-orange/15 text-xs text-orange-text my-7">
        <div className="w-1.5 h-1.5 rounded-full bg-orange-light" />
        Now in early access
      </div>

      {/* Heading */}
      <h1 className="relative z-10 text-[clamp(40px,7vw,80px)] font-bold tracking-[-2px] leading-[1.05] text-white max-w-6xl mb-6">
        Deploy AI trading agents.
        <br />
        <span className="text-orange-light">Any market. Any scale.</span>
      </h1>

      {/* Subtitle */}
      <p className="relative z-10 text-lg text-white/55 max-w-[540px] leading-relaxed mb-10">
        Artic is the orchestration hub for AI-powered trading. Launch agents on
        perps, spot, and prediction markets — manage everything from one place.
      </p>

      {/* Actions */}
      <div className="relative z-10 flex gap-3 items-center flex-wrap justify-center">
        <Link
          href="/docs/quickstart"
          className={cn(
            buttonVariants(),
            "bg-orange hover:bg-orange-hover text-white rounded-[10px] px-7 py-6 text-[15px] font-medium transition-transform hover:-translate-y-0.5"
          )}
        >
          Get early access
        </Link>
        <Link
          href="/docs"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "border-white/20 text-white/70 hover:border-white/50 hover:text-white rounded-[10px] px-7 py-6 text-[15px] font-medium bg-transparent"
          )}
        >
          Read the docs
        </Link>
      </div>

      <TerminalMockup />
    </section>
  );
}
