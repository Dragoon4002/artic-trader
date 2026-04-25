import Link from "next/link";
import Image from "next/image";
import { ArrowRight, GitBranch } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CtaBanner() {
  return (
    <section className="h-[80vh]">
      <div className="relative w-full h-full overflow-hidden isolate">
        {/* Background image */}
        <div className="absolute inset-0 -z-10">
          <Image
            src="/assets/footer-night.png"
            alt=""
            fill
            className="object-cover object-center"
            priority={false}
          />
          {/* Layered overlays for legibility */}
          {/* <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.5)_100%)]" /> */}
          {/* <div className="absolute inset-0 bg-gradient-to-b from-surface via-surface/40 to-transparent" /> */}
          {/* <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" /> */}
        </div>

        {/* Subtle accent glow */}
        {/* <div className="pointer-events-none absolute -top-20 left-1/2 -translate-x-1/2 w-[480px] h-[240px] rounded-full bg-orange/20 blur-[120px]" /> */}

        <div className="relative px-6 md:px-16 py-20 md:py-28 text-center h-full flex flex-col justify-center">
          <p className="text-xs tracking-[1.5px] uppercase text-gray mb-5">
            Get started
          </p>
          <h2 className="text-[clamp(40px,7vw,96px)] font-bold tracking-tight text-white mb-5 max-w-5xl mx-auto leading-[1.05]">
            Start trading with intelligence.
          </h2>
          <p className="text-[17px] text-white/60 mb-10 max-w-xl mx-auto leading-relaxed">
            Join the early access waitlist or self-host from GitHub today.
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/docs/quickstart"
              className={cn(
                buttonVariants(),
                "rounded-2xl text-white border border-cta-border bg-linear-to-b from-cta-light! to-cta! hover:from-cta! hover:to-cta-hover! px-7 h-12 text-[15px] font-semibold gap-2 transition-colors"
              )}
            >
              Get early access <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="https://github.com/Dragoon4002/Artic_trader"
              className={cn(
                buttonVariants({ variant: "outline" }),
                "border-white/20 text-white hover:border-white/40 hover:bg-white/5 rounded-full px-7 h-12 text-[15px] font-semibold bg-white/[0.04] backdrop-blur-sm gap-2"
              )}
            >
              <GitBranch className="w-4 h-4" /> View on GitHub
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
