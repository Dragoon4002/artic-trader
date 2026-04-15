import Link from "next/link";
import {
  Rocket,
  Layers,
  Settings,
  BookOpen,
  Server,
  Monitor,
  Container,
  Shield,
  TestTube,
  Terminal,
  LayoutGrid,
  Send,
  ArrowRight,
} from "lucide-react";
import type { ReactNode } from "react";

const sections: {
  icon: ReactNode;
  title: string;
  description: string;
  href: string;
  color: string;
}[] = [
  {
    icon: <Rocket className="h-5 w-5" />,
    title: "Quickstart",
    description: "Install, configure, and launch your first trading agent in under 5 minutes.",
    href: "/docs/quickstart",
    color: "bg-orange/20 text-orange-light",
  },
  {
    icon: <Layers className="h-5 w-5" />,
    title: "Architecture",
    description: "Hub-and-spoke topology, data flow, Docker containers, and key invariants.",
    href: "/docs/architecture",
    color: "bg-teal/20 text-teal-light",
  },
  {
    icon: <Settings className="h-5 w-5" />,
    title: "Agent Configuration",
    description: "All config options, risk parameters, LLM settings, and execution modes.",
    href: "/docs/agent-configuration",
    color: "bg-red/20 text-red-light",
  },
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "Strategy Catalog",
    description: "Browse 30+ quant algorithms across momentum, mean reversion, volatility, volume, and statistical categories.",
    href: "/docs/strategies",
    color: "bg-orange/20 text-orange-light",
  },
  {
    icon: <Server className="h-5 w-5" />,
    title: "Hub API Reference",
    description: "REST endpoints, WebSocket streaming, internal agent push APIs, and rate limits.",
    href: "/docs/hub-api",
    color: "bg-blue-accent/20 text-blue-light",
  },
  {
    icon: <Monitor className="h-5 w-5" />,
    title: "Client Guides",
    description: "Set up and use the TUI, CLI, Telegram bot, and REST API clients.",
    href: "/docs/clients",
    color: "bg-teal/20 text-teal-light",
  },
  {
    icon: <Terminal className="h-5 w-5" />,
    title: "CLI Reference",
    description: "Interactive menu-driven CLI for agent creation, monitoring, and management.",
    href: "/docs/cli-reference",
    color: "bg-orange/20 text-orange-light",
  },
  {
    icon: <LayoutGrid className="h-5 w-5" />,
    title: "TUI Reference",
    description: "Full keyboard-driven terminal UI with live dashboards, log viewer, and forms.",
    href: "/docs/tui-reference",
    color: "bg-teal/20 text-teal-light",
  },
  {
    icon: <Send className="h-5 w-5" />,
    title: "Telegram Reference",
    description: "All 14 slash commands for agent control and monitoring from Telegram.",
    href: "/docs/telegram-reference",
    color: "bg-red/20 text-red-light",
  },
  {
    icon: <Container className="h-5 w-5" />,
    title: "Deployment",
    description: "Docker Compose setup, PostgreSQL, migrations, environment variables, and production tips.",
    href: "/docs/deployment",
    color: "bg-red/20 text-red-light",
  },
  {
    icon: <Shield className="h-5 w-5" />,
    title: "Authentication & Secrets",
    description: "JWT and API key auth, AES-encrypted secret storage, and resolution order.",
    href: "/docs/authentication",
    color: "bg-blue-accent/20 text-blue-light",
  },
  {
    icon: <TestTube className="h-5 w-5" />,
    title: "Testing",
    description: "Test structure, conventions, mocking external services, and strategy contract verification.",
    href: "/docs/testing",
    color: "bg-orange/20 text-orange-light",
  },
];

export default function DocsIndex() {
  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-white mb-3">
        Documentation
      </h1>
      <p className="text-[17px] text-white/50 leading-relaxed mb-10 max-w-xl">
        Everything you need to deploy, configure, and operate AI trading agents with Artic.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {sections.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="group flex gap-4 p-5 rounded-xl border border-white/8 bg-white/3 transition-all duration-200 hover:border-orange-light/40 hover:bg-orange/6 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-orange/5"
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${s.color}`}>
              {s.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-white">{s.title}</h3>
                <ArrowRight className="h-3.5 w-3.5 text-white/30 group-hover:text-orange-light group-hover:translate-x-0.5 transition-all" />
              </div>
              <p className="text-[13px] text-white/45 leading-relaxed">{s.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
