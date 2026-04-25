"use client";

import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function Hero() {
  return (
    <section className="relative min-h-[88vh] flex flex-col items-center justify-center text-center px-6 py-40 overflow-hidden">
      {/* Gradient background */}
      {/* <div
        className="absolute inset-0 z-0"
        style={{
          background: `
            radial-gradient(ellipse 60% 50% at 50% 0%, rgba(218,119,86,0.25) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 20% 80%, rgba(29,158,117,0.12) 0%, transparent 60%),
            #0a0a0f
          `,
        }}
      /> */}
      <div className="absolute inset-0 bg-[url('/assets/sky.png')] bg-cover bg-center">
        {/* <motion.div>
          <Image
            src="/assets/foreground.png"
            alt="Hero Background"
            layout="fill"
            objectFit="cover"
            objectPosition="center"
            className="opacity-20"
          />
        </motion.div> */}
        <motion.div
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="absolute inset-0 bg-[url('/assets/foreground/2.png')] bg-cover bg-center blur-xs"
        />
        <motion.div
          initial={{ y: 100 }}
          animate={{ y: 10 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
          className="absolute inset-0 bg-[url('/assets/foreground/1.png')] bg-cover bg-center z-20"
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5, ease: "easeOut" }} 
        className="z-10 flex flex-col items-center justify-center text-center"
      >
        {/* Badge */}
        <div className="relative z-10 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-background/50 bg-background text-xs text- my-7">
          <div className="w-1.5 h-1.5 rounded-full bg-gray" />
          Now in early access
        </div>
        {/* Heading */}
        <h1 className="relative z-10 text-[clamp(40px,7vw,80px)] font-bold tracking-[-2px] leading-[1.05] text-background max-w-6xl mb-6">
          Deploy AI trading agents.
          <br />
          <span className="text-foreground-muted">Any market. Any scale.</span>
        </h1>
        {/* Subtitle */}
        <p className="relative z-10 text-xl text-background max-w-180 leading-relaxed mb-10">
          Artic is the orchestration hub for AI-powered trading. Launch agents on
          perps, spot, and prediction markets — manage everything from one place.
        </p>
        {/* Actions */}
        <div className="relative z-10 flex gap-3 items-center flex-wrap justify-center">
          <Link
            href="/docs/quickstart"
            className={cn(
              buttonVariants(),
              "rounded-2xl text-white border border-cta-border bg-linear-to-b from-cta-light! to-cta! hover:from-cta! hover:to-cta-hover! px-7 py-6 text-[15px] font-medium transition-all hover:-translate-y-0.5"
            )}
          >
            Get early access
          </Link>
          <Link
            href="/docs"
            className={cn(
              buttonVariants({ variant: "outline" }),
              "border-cta-hover! text-cta-hover bg-white! hover:border-cta-hover/50 hover:text-cta-hover/50 rounded-[10px] px-7 py-6 text-[15px] font-medium"
            )}
          >
            Read the docs
          </Link>
        </div>
      </motion.div>

      {/* <TerminalMockup /> */}
    </section>
  );
}
