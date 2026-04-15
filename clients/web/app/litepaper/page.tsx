"use client";

import { Navbar } from "@/components/landing/navbar";
import { Footer } from "@/components/landing/footer";
import Link from "next/link";
import { ArrowLeft, Clock, Calendar, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState, useRef } from "react";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { buttonVariants } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

/* ── Section definitions ───────────────────────────────────────────── */

const sections = [
  { id: "executive-summary", label: "Executive Summary" },
  { id: "problem-statement", label: "Problem Statement" },
  { id: "the-artic-solution", label: "The Artic Solution" },
  { id: "system-architecture", label: "System Architecture" },
  { id: "strategy-engine", label: "Strategy Engine" },
  { id: "risk-management", label: "Risk Management" },
  { id: "markets-integrations", label: "Markets & Integrations" },
  { id: "product-roadmap", label: "Product Roadmap" },
  { id: "risk-disclaimer", label: "Risk Disclaimer" },
];

/* ── Sidebar ───────────────────────────────────────────────────────── */

function LitepaperSidebar({ activeId }: { activeId: string }) {
  return (
    <aside className="hidden lg:block w-60 shrink-0 border-r border-white/8 sticky top-16 h-[calc(100vh-64px)]">
      <ScrollArea className="h-full">
        <nav className="py-8 pr-4 pl-6">
          <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4 font-semibold">
            Litepaper
          </p>
          <ul className="space-y-1">
            {sections.map((s, i) => (
              <li key={s.id}>
                <a
                  href={`#${s.id}`}
                  className={cn(
                    "block py-1.5 px-3 rounded-lg text-sm transition-colors",
                    activeId === s.id
                      ? "bg-orange/15 text-orange-text font-medium"
                      : "text-white/50 hover:text-white/80 hover:bg-white/5"
                  )}
                >
                  <span className="text-white/25 mr-2 font-mono text-xs">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {s.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </ScrollArea>
    </aside>
  );
}

function MobileLitepaperNav({ activeId }: { activeId: string }) {
  return (
    <div className="lg:hidden border-b border-white/8 px-4 py-2">
      <Sheet>
        <SheetTrigger
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "text-white/60 gap-2"
          )}
        >
          <Menu className="h-4 w-4" />
          <span className="text-sm">Sections</span>
        </SheetTrigger>
        <SheetContent side="left" className="bg-surface border-white/8 w-64">
          <SheetTitle className="sr-only">Litepaper Sections</SheetTitle>
          <nav className="mt-6">
            <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4 font-semibold px-2">
              Litepaper
            </p>
            <ul className="space-y-1">
              {sections.map((s, i) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    className={cn(
                      "block py-1.5 px-3 rounded-lg text-sm transition-colors",
                      activeId === s.id
                        ? "bg-orange/15 text-orange-text font-medium"
                        : "text-white/50 hover:text-white/80 hover:bg-white/5"
                    )}
                  >
                    <span className="text-white/25 mr-2 font-mono text-xs">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {s.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </SheetContent>
      </Sheet>
    </div>
  );
}

/* ── Helper components ─────────────────────────────────────────────── */

function Tag({ children }: { children: string }) {
  return (
    <span className="text-xs uppercase tracking-wider font-semibold text-orange-text bg-orange/15 px-3 py-1 rounded-full">
      {children}
    </span>
  );
}

function H2({ id, children }: { id: string; children: string }) {
  return (
    <h2
      id={id}
      className="text-3xl md:text-4xl font-bold text-white mt-20 mb-5 scroll-mt-24"
    >
      {children}
    </h2>
  );
}

function H3({ children }: { children: string }) {
  return (
    <h3 className="text-xl md:text-2xl font-semibold text-white mt-12 mb-4">
      {children}
    </h3>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-base text-white/60 leading-[1.85] mb-5">{children}</p>
  );
}

function Highlight({ children }: { children: string }) {
  return <span className="text-orange-text font-medium">{children}</span>;
}

function Callout({
  children,
  variant = "info",
}: {
  children: React.ReactNode;
  variant?: "info" | "warning";
}) {
  const border =
    variant === "warning" ? "border-red/30" : "border-orange/30";
  const bg = variant === "warning" ? "bg-red/10" : "bg-orange/10";
  const text =
    variant === "warning" ? "text-red-light" : "text-orange-text";
  return (
    <div className={`my-8 p-6 rounded-xl border ${border} ${bg}`}>
      <p className={`text-[15px] ${text} leading-relaxed`}>{children}</p>
    </div>
  );
}

function Code({ children }: { children: string }) {
  return (
    <code className="text-[15px] text-orange-text bg-orange/15 px-1.5 py-0.5 rounded font-mono">
      {children}
    </code>
  );
}

function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: { cells: string[]; color?: string }[];
}) {
  return (
    <div className="overflow-x-auto my-10 rounded-2xl border border-white/10 bg-white/2 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.3)]">
      <table className="w-full text-[15px]">
        <thead>
          <tr className="border-b border-white/10 bg-white/5">
            {headers.map((h) => (
              <th
                key={h}
                className="text-left text-sm text-white/60 font-semibold px-5 py-4 uppercase tracking-wider"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-white/6 last:border-0 hover:bg-white/3 transition-colors"
            >
              {row.cells.map((cell, j) => (
                <td
                  key={j}
                  className={cn(
                    "px-5 py-4",
                    j === 0 && row.color
                      ? `${row.color} font-medium`
                      : "text-white/55"
                  )}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StepCard({
  step,
  title,
  desc,
}: {
  step: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="flex gap-5 p-5 rounded-xl border border-white/8 bg-white/3">
      <span className="text-2xl font-bold text-orange/50 font-mono shrink-0">
        {step}
      </span>
      <div>
        <p className="text-[15px] font-semibold text-white mb-1">{title}</p>
        <p className="text-[15px] text-white/45 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

/* ── Page ───────────────────────────────────────────────────────────── */

export default function LitepaperPage() {
  const [activeId, setActiveId] = useState(sections[0].id);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        }
      },
      { rootMargin: "-20% 0px -60% 0px", threshold: 0 }
    );

    for (const s of sections) {
      const el = document.getElementById(s.id);
      if (el) observerRef.current.observe(el);
    }

    return () => observerRef.current?.disconnect();
  }, []);

  return (
    <>
      <Navbar />
      <div className="flex flex-1 min-h-[calc(100vh-64px)] pt-16">
        <LitepaperSidebar activeId={activeId} />
        <div className="flex-1 flex flex-col">
          <MobileLitepaperNav activeId={activeId} />
          <main className="flex-1 max-w-5xl mx-auto w-full px-6 md:px-10 py-10">
            {/* Back */}
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mb-10"
            >
              <ArrowLeft className="w-4 h-4" />
              Home
            </Link>

            {/* Header */}
            <div className="flex flex-wrap gap-2 mb-6">
              <Tag>Litepaper</Tag>
              <Tag>Architecture</Tag>
              <Tag>v1.0</Tag>
            </div>

            <h1 className="text-[clamp(32px,5vw,52px)] font-bold tracking-tight text-white leading-[1.15] mb-4">
              Artic: AI-Powered Multi-Agent Trading Platform
            </h1>
            <p className="text-xl text-white/45 mb-6">
              Deploy intelligent trading agents across any market — managed from
              a single hub.
            </p>

            <div className="flex items-center gap-5 text-sm text-white/30 mb-14">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                April 2026
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                15 min read
              </span>
            </div>

            <div className="h-px bg-white/8 mb-14" />

            {/* ─── 1. Executive Summary ─────────────────────────────── */}
            <H2 id="executive-summary">1. Executive Summary</H2>

            <P>
              Artic abstracts the complexity of quantitative trading into a
              deployable, configurable agent. Where traditional bots require
              manual strategy selection and parameter tuning, Artic&apos;s LLM
              oversight layer continuously evaluates market regime, selects the
              optimal strategy from a library of{" "}
              <Highlight>23 signal algorithms across 5 categories</Highlight>,
              and adapts on a configurable schedule — without human intervention.
            </P>

            <P>The platform is designed around three core principles:</P>

            <div className="my-5 space-y-3">
              {[
                [
                  "Autonomy",
                  "Agents make independent, data-driven decisions within user-defined risk parameters.",
                ],
                [
                  "Modularity",
                  "Every component — strategy, LLM provider, executor, client interface — is independently replaceable.",
                ],
                [
                  "Transparency",
                  "All agent decisions, trade logs, and LLM reasoning are observable in real time across every client interface.",
                ],
              ].map(([title, desc]) => (
                <div key={title} className="flex gap-4">
                  <span className="text-orange-text font-semibold text-[15px] shrink-0 w-32">
                    {title}
                  </span>
                  <span className="text-[15px] text-white/50">{desc}</span>
                </div>
              ))}
            </div>

            <Callout>
              Artic ships 23 signal algorithms + 4 utility functions (risk
              sizing, session filters), persists state in PostgreSQL, and uses
              push-based telemetry from agents to hub.
            </Callout>

            {/* ─── 2. Problem Statement ────────────────────────────── */}
            <H2 id="problem-statement">2. Problem Statement</H2>

            <H3>The Gap Between AI and Execution</H3>

            <P>
              Algorithmic trading has long been the domain of institutional
              players with the engineering resources to build, maintain, and
              monitor complex systems. Retail traders and independent quants face
              a fragmented landscape: strategy research tools exist in isolation
              from execution infrastructure, LLM-based market analysis remains
              disconnected from live trading systems, and deploying multiple
              concurrent strategies requires managing sprawling, brittle
              codebases.
            </P>

            <P>Specifically, the market lacks a platform that:</P>

            <ul className="list-disc list-inside text-base text-white/55 leading-[1.85] mb-5 space-y-1.5 pl-2">
              <li>
                Connects LLM intelligence directly to a live execution engine
                without manual intermediary steps.
              </li>
              <li>
                Enables concurrent multi-agent, multi-strategy deployment from a
                single control surface.
              </li>
              <li>
                Provides full observability — trade logs, LLM reasoning,
                position state — without requiring infrastructure expertise.
              </li>
              <li>
                Allows strategy research and live execution to share the same
                runtime environment.
              </li>
            </ul>

            <P>
              Existing solutions — centralised copy-trading platforms, isolated
              strategy bots, and LLM-wrapped price feeds — address fragments of
              this problem. None orchestrate the full lifecycle from intelligent
              strategy selection through to live execution and monitoring at the
              agent level.
            </P>

            {/* ─── 3. The Artic Solution ───────────────────────────── */}
            <H2 id="the-artic-solution">3. The Artic Solution</H2>

            <H3>One Hub. Many Agents.</H3>

            <P>
              Artic introduces a hub-and-agent model where a central server (the
              Hub) maintains authority over all deployed agents. Each agent is an
              isolated Docker container — running locally or on a remote VM —
              with its own configuration, market scope, and strategy assignment.
              The Hub handles registration, lifecycle management, persistent
              state, and all client communication.
            </P>

            <P>
              Users interact through whichever interface suits their workflow — a
              terminal UI, a web dashboard, a CLI, or a Telegram bot. All
              interfaces communicate with the Hub via a REST + WebSocket API. No
              interface has direct access to agents, ensuring a consistent,
              auditable control plane.
            </P>

            <P>
              Communication between agents and the Hub is{" "}
              <Highlight>push-based</Highlight>. Agents POST status updates to
              the Hub every tick, push trade records on position open/close, and
              batch log entries every 10 ticks. The Hub never polls agents — all
              telemetry flows inward.
            </P>

            <H3>The LLM as Market Intelligence</H3>

            <P>
              At the core of each agent sits an LLM planning loop. On
              initialisation, the agent ingests historical OHLCV data and live
              price feeds, then prompts the configured LLM to assess market
              regime and select the most appropriate strategy from the active
              library. This evaluation recurs on a user-defined schedule —
              allowing the agent to shift strategy as market conditions evolve.
            </P>

            <P>
              The LLM does not execute trades. Its role is advisory and
              supervisory: it reads structured market data, reasons about
              conditions, and outputs a strategy identifier with configuration
              parameters. The execution engine computes a signal via the selected
              strategy and acts on it within the risk parameters set at agent
              configuration time.
            </P>

            <P>
              Every strategy in the library returns a normalised{" "}
              <Highlight>signal</Highlight> (a float between −1 and +1, where
              positive = bullish, negative = bearish, zero = neutral) paired with
              a diagnostic detail string. This uniform contract lets the engine
              treat all 23 algorithms identically regardless of their internal
              complexity.
            </P>

            <H3>Paper Trading & Safe Experimentation</H3>

            <P>
              Paper trading is the default mode. It uses identical strategy
              logic, LLM decision-making, and position tracking as live mode —
              but routes all order execution through a simulation layer. This
              allows users to validate strategy behaviour, observe LLM
              decision-making, and gain confidence before deploying real capital.
            </P>

            {/* ─── 4. System Architecture ──────────────────────────── */}
            <H2 id="system-architecture">4. System Architecture</H2>

            <P>
              Artic is structured across six primary components. Each is
              independently deployable and communicates through well-defined
              interfaces:
            </P>

            <Table
              headers={["Component", "Stack", "Role"]}
              rows={[
                {
                  cells: [
                    "Hub",
                    "Python / FastAPI",
                    "Agent lifecycle, auth, market cache, REST + WebSocket API",
                  ],
                  color: "text-orange-text",
                },
                {
                  cells: [
                    "Agent (App)",
                    "Python / FastAPI",
                    "Per-symbol trading engine, runs inside Docker container",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "LLM Planner",
                    "Multi-provider",
                    "Market regime analysis, strategy selection, position supervision",
                  ],
                  color: "text-red-light",
                },
                {
                  cells: [
                    "Market Feeds",
                    "Pyth + TwelveData",
                    "Real-time price oracle + OHLCV historical candles",
                  ],
                  color: "text-blue-light",
                },
                {
                  cells: [
                    "Database",
                    "PostgreSQL",
                    "Trade history, agent configs, user settings, position snapshots",
                  ],
                  color: "text-orange-light",
                },
                {
                  cells: [
                    "Clients",
                    "TUI / CLI / Web / Telegram",
                    "All control surfaces talk to Hub API — no direct agent access",
                  ],
                  color: "text-teal-light",
                },
              ]}
            />

            <H3>Database</H3>

            <P>
              The Hub persists all state in{" "}
              <Highlight>PostgreSQL via SQLAlchemy async</Highlight> with Alembic
              migrations. The schema includes 9 models across core tables:{" "}
              <Code>users</Code>, <Code>agents</Code>, <Code>trades</Code>,{" "}
              <Code>log_entries</Code>, <Code>market_cache</Code>,{" "}
              <Code>user_secrets</Code>, <Code>agent_secret_overrides</Code>,
              and <Code>onchain_decisions</Code>. Log entries are append-only and
              bulk-inserted every 10 ticks for write efficiency.
            </P>

            <H3>Authentication</H3>

            <P>
              Artic uses a{" "}
              <Highlight>dual-method authentication</Highlight> system. The
              Hub&apos;s auth dependency tries JWT first, then falls back to API
              key:
            </P>

            <div className="my-5 space-y-3">
              <StepCard
                step="01"
                title="JWT Auth (TUI, Web Dashboard)"
                desc="Users authenticate via POST /auth/login with email + password. Hub verifies bcrypt hash, issues a JWT access token (15-minute expiry) + refresh token. Clients include the token as Authorization: Bearer header."
              />
              <StepCard
                step="02"
                title="API Key Auth (CLI, Telegram)"
                desc="Users generate a key via POST /api/keys. Hub stores a SHA-256 hash in users.api_key_hash and returns the raw key once (artic_ prefix). Clients include the key as X-API-Key header. Lost key = regenerate."
              />
              <StepCard
                step="03"
                title="Internal Auth (Agent → Hub)"
                desc="Agent containers authenticate to /internal/* endpoints with X-Internal-Secret header. The secret is injected as a Docker environment variable at spawn time and matches the Hub's INTERNAL_SECRET."
              />
            </div>

            <H3>Agent Registry & Communication</H3>

            <P>
              The Hub maintains an agent registry — a live record of all running,
              paused, and completed agents. Communication is entirely{" "}
              <Highlight>push-based</Highlight>: agents push state to the Hub,
              the Hub never polls.
            </P>

            <Table
              headers={["Endpoint", "Auth", "Frequency"]}
              rows={[
                {
                  cells: [
                    "POST /internal/agents/{id}/status",
                    "X-Internal-Secret",
                    "Every tick",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "POST /internal/trades",
                    "X-Internal-Secret",
                    "On position open / close",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "POST /internal/logs",
                    "X-Internal-Secret",
                    "Every 10 ticks (batched)",
                  ],
                  color: "text-teal-light",
                },
              ]}
            />

            <P>
              If an agent container crashes, trade history is preserved in full
              in PostgreSQL; only the live in-memory position state is lost.
            </P>

            {/* ─── 5. Strategy Engine ──────────────────────────────── */}
            <H2 id="strategy-engine">5. Strategy Engine</H2>

            <H3>23 Signal Algorithms</H3>

            <P>
              The strategy library is Artic&apos;s core quantitative layer.
              Algorithms are organised into five functional categories, each
              targeting a different market regime or signal type. The LLM planner
              selects among these based on its analysis of current conditions:
            </P>

            <Table
              headers={["Category", "Count", "Algorithms"]}
              rows={[
                {
                  cells: [
                    "Momentum",
                    "10",
                    "simple_momentum, dual_momentum, breakout, donchian_channel, ma_crossover, ema_crossover, macd_signal, adx_filter, supertrend, ichimoku_signal",
                  ],
                  color: "text-orange-text",
                },
                {
                  cells: [
                    "Mean Reversion",
                    "5",
                    "z_score, bollinger_reversion, rsi_signal, stochastic_signal, range_sr",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "Volatility",
                    "3",
                    "atr_breakout, bollinger_squeeze, keltner_bollinger",
                  ],
                  color: "text-red-light",
                },
                {
                  cells: [
                    "Volume / Order Flow",
                    "3",
                    "vwap_deviation, obv_trend, funding_bias_stub",
                  ],
                  color: "text-blue-light",
                },
                {
                  cells: [
                    "Statistical",
                    "2",
                    "linear_regression_channel, kalman_fair_value",
                  ],
                  color: "text-orange-light",
                },
              ]}
            />

            <P>
              In addition to signal algorithms, the library exports 4 utility
              functions: <Code>kelly_size</Code> and{" "}
              <Code>vol_scaling_mult</Code> for risk sizing, plus{" "}
              <Code>session_filter</Code> and <Code>day_of_week_filter</Code>{" "}
              for time-based filtering — 27 total exports.
            </P>

            <H3>Signal Contract</H3>

            <P>
              Every strategy exposes a standard interface. It accepts price
              history and/or OHLCV candle data as input and returns a tuple:
            </P>

            <div className="my-8 p-6 rounded-2xl border border-white/10 bg-white/3 font-mono text-base shadow-[0_4px_24px_-4px_rgba(0,0,0,0.3)]">
              <p className="text-white/70">
                <span className="text-orange-text">def</span>{" "}
                <span className="text-teal-light">strategy</span>(prices,
                candles, **params) →{" "}
                <span className="text-red-light">
                  (signal: float, detail: str)
                </span>
              </p>
              <div className="mt-4 text-sm text-white/40 space-y-1.5">
                <p>
                  signal &gt; 0 → bullish &nbsp;|&nbsp; signal &lt; 0 → bearish
                  &nbsp;|&nbsp; signal = 0 → neutral
                </p>
                <p>
                  signal range: [−1, +1] &nbsp;|&nbsp; detail: diagnostic string
                  for logging
                </p>
              </div>
            </div>

            <P>
              The execution engine and the risk layer consume these outputs
              uniformly, regardless of which strategy is active. The dispatcher
              in <Code>signals.py</Code> routes a strategy name to the correct
              algorithm function.
            </P>

            <H3>LLM Strategy Selection Flow</H3>

            <div className="my-8 space-y-3">
              <StepCard
                step="01"
                title="Context Assembly"
                desc="Agent gathers price history, OHLCV candles, and a structured market summary including recent returns, volatility, and volume metrics."
              />
              <StepCard
                step="02"
                title="LLM Evaluation"
                desc="Structured context is sent to the configured LLM provider. The model reasons about market regime and selects the most appropriate strategy."
              />
              <StepCard
                step="03"
                title="Strategy Output"
                desc="LLM returns a strategy identifier, lookback period, entry threshold, and max_loss_pct. These parameters configure the selected algorithm."
              />
              <StepCard
                step="04"
                title="Signal Computation"
                desc="compute_strategy_signal() dispatches to the selected algorithm. The engine receives a normalised signal and decides: OPEN_LONG, OPEN_SHORT, CLOSE, or HOLD."
              />
              <StepCard
                step="05"
                title="Re-evaluation"
                desc="At a user-defined interval, the loop restarts. The LLM re-evaluates conditions and may switch strategies, adjust parameters, or modify stop-loss / take-profit levels."
              />
            </div>

            {/* ─── 6. Risk Management ──────────────────────────────── */}
            <H2 id="risk-management">6. Risk Management</H2>

            <P>
              Every Artic agent operates within a risk framework configured at
              deployment time via the <Code>risk_params</Code> JSONB column on
              the agents table.
            </P>

            <H3>Implemented Controls</H3>

            <div className="my-5 space-y-3">
              <StepCard
                step="SL"
                title="Stop-Loss"
                desc="Supports both percentage-based (fixed sl_pct) and price-based (dynamic, ATR-derived) stop-loss. Checked every tick — position closes immediately when hit."
              />
              <StepCard
                step="TP"
                title="Take-Profit"
                desc="Percentage-based (fixed tp_pct) or price-based with configurable risk-reward ratio. The LLM's max_loss_pct serves as fallback when no explicit SL is set."
              />
              <StepCard
                step="SV"
                title="LLM Supervisor"
                desc="A secondary LLM check runs every N seconds on open positions. It can KEEP the position, CLOSE it, or ADJUST_TP_SL dynamically based on evolving conditions."
              />
              <StepCard
                step="PT"
                title="Paper Trading Default"
                desc="All agents initialise in paper trading mode. Live execution requires explicit user opt-in with funded exchange credentials."
              />
            </div>

            <Callout variant="warning">
              Drawdown stops and a remote kill switch are on the development
              roadmap but are not yet implemented in the current codebase. Risk
              management currently relies on per-position SL/TP and LLM
              supervisor checks.
            </Callout>

            {/* ─── 7. Markets & Integrations ───────────────────────── */}
            <H2 id="markets-integrations">
              7. Supported Markets & Integrations
            </H2>

            <P>
              Artic&apos;s integration layer is designed to be executor-agnostic.
              Any market or exchange that exposes a compatible order interface can
              be added as an executor module.
            </P>

            <Table
              headers={["Provider", "Purpose", "Status"]}
              rows={[
                {
                  cells: [
                    "OpenAI / Anthropic / DeepSeek / Gemini",
                    "LLM providers — strategy selection, regime analysis",
                    "Live",
                  ],
                  color: "text-orange-text",
                },
                {
                  cells: [
                    "Pyth Network (Hermes)",
                    "Real-time on-chain price feeds",
                    "Live",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "TwelveData",
                    "OHLCV historical candles (cached via Hub, 60s staleness)",
                    "Live",
                  ],
                  color: "text-blue-light",
                },
                {
                  cells: [
                    "CoinMarketCap",
                    "Token metadata and market data",
                    "Live",
                  ],
                  color: "text-red-light",
                },
                {
                  cells: [
                    "HashKey Global",
                    "Perpetual futures execution — primary mainnet integration",
                    "In Progress",
                  ],
                  color: "text-orange-light",
                },
              ]}
            />

            <P>
              HashKey Global serves as the primary live execution target. Its
              perpetuals API provides order placement, position management,
              funding rate data, and balance queries — mapping directly to
              Artic&apos;s BaseExecutor interface. The sandbox environment is
              used for integration testing prior to mainnet deployment.
            </P>

            {/* ─── 8. Roadmap ──────────────────────────────────────── */}
            <H2 id="product-roadmap">8. Product Roadmap</H2>

            <Table
              headers={["Phase", "Milestone", "Status"]}
              rows={[
                {
                  cells: [
                    "Q1",
                    "Core Agent Framework — single-agent deployment, full strategy library (23 algos), LLM oversight loop, paper trading, TUI + CLI clients",
                    "Live",
                  ],
                  color: "text-teal-light",
                },
                {
                  cells: [
                    "Q2",
                    "Multi-Agent & Mainnet — multi-agent orchestration from a single hub, VM deployment, live execution on HashKey Global perps, web dashboard + Telegram bot",
                    "In Progress",
                  ],
                  color: "text-orange-text",
                },
                {
                  cells: [
                    "Q3",
                    "Strategy Marketplace — user-created strategies listed and sold on-platform, performance attribution, revenue sharing for authors",
                    "Planned",
                  ],
                  color: "text-white/40",
                },
                {
                  cells: [
                    "Q4",
                    "Multi-Sector Expansion — futures, equities, options, prediction markets. Sector-specific LLM prompting and strategy libraries",
                    "Planned",
                  ],
                  color: "text-white/40",
                },
              ]}
            />

            <P>
              The Strategy Marketplace (Q3) transforms Artic from a personal
              trading tool into a collaborative ecosystem where quantitative
              researchers distribute and monetise their work. The multi-sector
              expansion (Q4) extends the addressable market beyond crypto
              derivatives into traditional finance instruments.
            </P>

            {/* ─── 9. Disclaimer ───────────────────────────────────── */}
            <H2 id="risk-disclaimer">9. Risk Disclaimer</H2>

            <div className="my-8 p-8 rounded-2xl border border-white/10 bg-white/2 space-y-5 text-[15px] text-white/40 leading-relaxed shadow-[0_4px_24px_-4px_rgba(0,0,0,0.3)]">
              <p>
                Paper trading simulations do not involve real money and do not
                guarantee future performance of any strategy. Past backtesting
                results and simulated outcomes are not indicative of future
                results. Cryptocurrency and derivatives markets are highly
                volatile. Users who choose to deploy Artic agents in live trading
                mode do so at their own risk and are solely responsible for any
                financial outcomes.
              </p>
              <p>
                Artic does not custody user funds. Private keys, wallet
                credentials, and exchange API keys remain under the sole control
                of the user at all times. The Artic team assumes no liability for
                losses arising from the use of this software.
              </p>
              <p>
                Risk management currently relies on per-position stop-loss and
                take-profit levels with LLM supervisor checks. Additional risk
                controls including drawdown stops and remote kill switches are
                under active development.
              </p>
              <p>
                This document does not constitute an offering of securities,
                tokens, or any regulated financial instrument. Artic has no token
                at this time. Nothing in this document should be construed as a
                solicitation to invest.
              </p>
            </div>

            <div className="h-px bg-white/8 mt-20 mb-10" />

            <div className="flex items-center justify-between">
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Home
              </Link>
              <p className="text-sm text-white/20">
                Artic &middot; AI Trading Agent Orchestration Platform
              </p>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}
