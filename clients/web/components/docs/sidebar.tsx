"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { docsNav, type NavGroup } from "@/lib/docs-nav";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronRight } from "lucide-react";

function SidebarGroup({ group }: { group: NavGroup }) {
  const pathname = usePathname();
  const isActive = group.items.some((item) => item.href === pathname);
  const [open, setOpen] = useState(group.defaultOpen || isActive);

  useEffect(() => {
    if (isActive && !open) setOpen(true);
  }, [isActive]);

  return (
    <li>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 w-full py-1.5 px-3 text-xs font-semibold uppercase tracking-wide text-white/40 hover:text-white/60 transition-colors"
      >
        <ChevronRight
          className={cn(
            "h-3 w-3 transition-transform duration-200",
            open && "rotate-90"
          )}
        />
        {group.title}
      </button>
      {open && (
        <ul className="mt-0.5 space-y-0.5">
          {group.items.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "block py-1.5 px-3 pl-7 rounded-lg text-sm transition-colors",
                  pathname === item.href
                    ? "bg-orange/15 text-orange-text font-medium"
                    : "text-white/50 hover:text-white/80 hover:bg-white/5"
                )}
              >
                {item.title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function DocsSidebar() {
  return (
    <aside className="hidden lg:block w-60 shrink-0 border-r border-white/8 sticky top-16 h-[calc(100vh-64px)]">
      <ScrollArea className="h-full">
        <nav className="py-8 pr-4 pl-6">
          <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4 font-semibold">
            Documentation
          </p>
          <ul className="space-y-2">
            {docsNav.map((group) => (
              <SidebarGroup key={group.title} group={group} />
            ))}
          </ul>
        </nav>
      </ScrollArea>
    </aside>
  );
}
