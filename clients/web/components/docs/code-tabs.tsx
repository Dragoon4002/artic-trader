"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ReactNode } from "react";

interface CodeTabProps {
  tabs: { label: string; content: ReactNode }[];
}

export function CodeTabs({ tabs }: CodeTabProps) {
  return (
    <Tabs defaultValue={tabs[0]?.label} className="my-4">
      <TabsList className="bg-white/5 border border-white/8 rounded-lg p-0.5">
        {tabs.map((t) => (
          <TabsTrigger
            key={t.label}
            value={t.label}
            className="text-xs px-3 py-1.5 text-white/50 data-[state=active]:bg-orange/20 data-[state=active]:text-orange-text rounded-md"
          >
            {t.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs.map((t) => (
        <TabsContent key={t.label} value={t.label} className="mt-3">
          {t.content}
        </TabsContent>
      ))}
    </Tabs>
  );
}
