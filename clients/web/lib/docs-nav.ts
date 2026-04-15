export type NavItem = {
  title: string;
  href: string;
};

export type NavGroup = {
  title: string;
  items: NavItem[];
  defaultOpen?: boolean;
};

export const docsNav: NavGroup[] = [
  {
    title: "Getting Started",
    defaultOpen: true,
    items: [
      { title: "Overview", href: "/docs" },
      { title: "Quickstart", href: "/docs/quickstart" },
    ],
  },
  {
    title: "Core Concepts",
    items: [
      { title: "Architecture", href: "/docs/architecture" },
      { title: "Agent Configuration", href: "/docs/agent-configuration" },
      { title: "Strategy Catalog", href: "/docs/strategies" },
    ],
  },
  {
    title: "API & Clients",
    items: [
      { title: "Hub API Reference", href: "/docs/hub-api" },
      { title: "Authentication", href: "/docs/authentication" },
      { title: "Client Guides", href: "/docs/clients" },
      { title: "CLI Reference", href: "/docs/cli-reference" },
      { title: "TUI Reference", href: "/docs/tui-reference" },
      { title: "Telegram Reference", href: "/docs/telegram-reference" },
    ],
  },
  {
    title: "Operations",
    items: [
      { title: "Deployment", href: "/docs/deployment" },
      { title: "Testing", href: "/docs/testing" },
    ],
  },
];
