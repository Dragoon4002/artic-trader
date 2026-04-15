import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CtaBanner() {
  return (
    <div className="relative mx-6 md:mx-12 mb-24 p-12 md:p-16 rounded-[20px] text-center">
      <div className="fixed top-8 left-3/12 w-80 h-60 rounded-full bg-amber-600/20 blur-[50px] -z-10"/>
      <h2 className="text-[clamp(24px,4vw,40px)] font-bold text-white mb-4 tracking-tight">
        Start trading with intelligence.
      </h2>
      <p className="text-[17px] text-white/50 mb-9">
        Join the early access waitlist or self-host from GitHub today.
      </p>
      <div className="flex gap-3 justify-center flex-wrap">
        <Link
          href="/docs/quickstart"
          className={cn(
            buttonVariants(),
            "bg-orange hover:bg-orange-hover text-white rounded-[10px] px-7 py-6 text-[15px] font-medium"
          )}
        >
          Get early access
        </Link>
        <Link
          href="#"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "border-white/20 text-white/70 hover:border-white/50 hover:text-white rounded-[10px] px-7 py-6 text-[15px] font-medium bg-transparent"
          )}
        >
          View on GitHub
        </Link>
      </div>
    </div>
  );
}
