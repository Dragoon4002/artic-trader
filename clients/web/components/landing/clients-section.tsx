import { ClientCard } from "./client-card";

const clients = [
  {
    tag: "Web Dashboard",
    tagColor: "orange",
    title: "Full-featured browser UI",
    description:
      "Visual P&L charts, agent status cards, strategy inspector, and one-click deploy. Built for power users who want the full picture.",
  },
  {
    tag: "CLI & TUI",
    tagColor: "teal",
    title: "Terminal-native control",
    description:
      "Launch, inspect, and manage agents from your terminal. Full rich TUI with live log streaming and keyboard shortcuts.",
  },
  {
    tag: "Telegram Bot",
    tagColor: "red",
    title: "Alerts & commands on the go",
    description:
      "Get trade notifications, P&L snapshots, and stop any agent — all via Telegram. No laptop required.",
  },
  {
    tag: "REST API",
    tagColor: "blue",
    title: "Build on top of Artic",
    description:
      "Full REST + WebSocket API. Integrate Artic into your own tooling, scripts, or custom dashboards with zero friction.",
  },
];

export function ClientsSection() {
  return (
    <section className="pb-24 px-6 md:px-12 max-w-[1200px] mx-auto">
      <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4">
        Access your agents everywhere
      </p>
      <h2 className="text-[clamp(28px,4vw,44px)] font-bold tracking-tight text-white mb-4">
        Your interface. Your choice.
      </h2>
      <p className="text-[17px] text-white/50 max-w-[520px] leading-relaxed">
        Artic meets you where you are — terminal, browser, or Telegram.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-14">
        {clients.map((c) => (
          <ClientCard key={c.tag} {...c} />
        ))}
      </div>
    </section>
  );
}
