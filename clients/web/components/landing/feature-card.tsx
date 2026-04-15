import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

const iconColors: Record<string, string> = {
  orange: "bg-orange/20 text-orange-light",
  teal: "bg-teal/20 text-teal-light",
  red: "bg-red/20 text-red-light",
  blue: "bg-blue-accent/20 text-blue-light",
};

const decorColors: Record<string, string> = {
  orange: "bg-orange-light",
  teal: "bg-teal-light",
  red: "bg-red-light",
  blue: "bg-blue-light",
};

interface FeatureCardProps {
  icon: ReactNode;
  color: string;
  title: string;
  description: string;
  hoverBg: string;
  visualGradient: string;
}

export function FeatureCard({ icon, color, title, description, hoverBg, visualGradient }: FeatureCardProps) {
  return (
    <div className="group rounded-[20px] border border-white/[0.06] bg-white/[0.02] hover-lift hover:border-white/[0.1] overflow-hidden flex flex-col">
      {/* Visual header area */}
      <div className={cn(
        "relative aspect-[16/9] sm:aspect-[4/3] flex items-center justify-center overflow-hidden transition-colors duration-300",
        `bg-gradient-to-br ${visualGradient}`,
        hoverBg
      )}>
        {/* Enlarged icon */}
        <div className={cn(
          "w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 group-hover:scale-[1.2]",
          iconColors[color]
        )}>
          <div className="[&>svg]:h-7 [&>svg]:w-7">
            {icon}
          </div>
        </div>

        {/* Decorative circle — top right */}
        <div className={cn(
          "absolute -top-4 -right-4 w-20 h-20 rounded-full opacity-[0.15] transition-transform duration-500 group-hover:scale-110",
          decorColors[color]
        )} />

        {/* Decorative circle — bottom left */}
        <div className={cn(
          "absolute -bottom-3 -left-3 w-14 h-14 rounded-full opacity-[0.1] transition-transform duration-500 group-hover:scale-125 group-hover:translate-x-1",
          decorColors[color]
        )} />
      </div>

      {/* Text content */}
      <div className="p-7 pt-5">
        <h3 className="text-base font-semibold text-white mb-2.5">{title}</h3>
        <p className="text-sm text-white/50 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
