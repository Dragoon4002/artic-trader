import { Navbar } from "@/components/landing/navbar";
import { Footer } from "@/components/landing/footer";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function JobsPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-32 text-center">
        <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4">
          Careers
        </p>
        <h1 className="text-[clamp(28px,5vw,48px)] font-bold tracking-tight text-white mb-4">
          Join Artic
        </h1>
        <p className="text-lg text-white/50 max-w-md leading-relaxed mb-10">
          We&apos;re building the future of AI-powered trading. No open positions
          right now — check back soon.
        </p>
        <div className="p-8 rounded-[14px] border border-white/[0.08] bg-white/[0.03] max-w-md w-full mb-10">
          <p className="text-white/40 text-sm">
            Follow us on Twitter / X for updates on open roles and company news.
          </p>
        </div>
        <Link
          href="/"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "border-white/20 text-white/70 hover:border-white/50 hover:text-white rounded-[10px] px-7 py-5 bg-transparent"
          )}
        >
          ← Back to home
        </Link>
      </main>
      <Footer />
    </>
  );
}
