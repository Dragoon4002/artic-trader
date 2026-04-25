import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const tagStyles: Record<string, string> = {
  orange: "bg-orange/20 text-orange-text border-transparent",
  teal: "bg-teal/20 text-teal-light border-transparent",
  red: "bg-red/20 text-red-light border-transparent",
  blue: "bg-blue-accent/20 text-blue-light border-transparent",
};

interface ClientCardProps {
  tag: string;
  tagColor: string;
  title: string;
  description: string;
}

export function ClientCard({ tag, tagColor, title, description }: ClientCardProps) {
  return (
    <div className="p-7 rounded-[14px] border border-white/8 bg-white/3 transition-all duration-200 hover:border-gray/40 hover:bg-orange/6 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-orange/5">
      <Badge
        className={cn(
          "mb-3.5 text-[11px] font-semibold tracking-wide uppercase",
          tagStyles[tagColor]
        )}
      >
        {tag}
      </Badge>
      <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-white/50 leading-relaxed">{description}</p>
    </div>
  );
}
