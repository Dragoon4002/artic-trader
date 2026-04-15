import { cn } from "@/lib/utils";
import { Info, AlertTriangle, Lightbulb } from "lucide-react";
import type { ReactNode } from "react";

const styles = {
  info: {
    border: "border-blue-accent/30",
    bg: "bg-blue-accent/5",
    icon: <Info className="h-4 w-4 text-blue-light" />,
    title: "text-blue-light",
  },
  warning: {
    border: "border-red/30",
    bg: "bg-red/5",
    icon: <AlertTriangle className="h-4 w-4 text-red-light" />,
    title: "text-red-light",
  },
  tip: {
    border: "border-teal/30",
    bg: "bg-teal/5",
    icon: <Lightbulb className="h-4 w-4 text-teal-light" />,
    title: "text-teal-light",
  },
};

export function Callout({
  type = "info",
  title,
  children,
}: {
  type?: "info" | "warning" | "tip";
  title?: string;
  children: ReactNode;
}) {
  const s = styles[type];
  return (
    <div className={cn("my-4 rounded-lg border p-4", s.border, s.bg)}>
      <div className="flex gap-2.5 items-start">
        <div className="mt-0.5 shrink-0">{s.icon}</div>
        <div className="min-w-0">
          {title && (
            <p className={cn("text-sm font-semibold mb-1", s.title)}>
              {title}
            </p>
          )}
          <div className="text-[13px] text-white/60 leading-relaxed [&>p]:mb-0">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
