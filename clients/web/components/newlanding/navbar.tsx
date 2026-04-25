"use client";

import { useState, useRef, type ReactNode } from "react";
import Link from "next/link";
import {
  Menu,
  X,
  ChevronDown,
  FileText,
  FileTerminal,
  ScrollText,
  Terminal,
  SquareTerminal,
  Send,
  Briefcase,
  GitBranch,
  ArrowRightIcon,
} from "lucide-react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import { Logo } from "@/components/shared/logo";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

// --- Types ---

type DropdownItem = {
  name: string;
  desc: string;
  href: string;
  icon: ReactNode;
  colors: [string, string];
};

type DropdownGroup = { heading: string; items: DropdownItem[] };

type NavItem =
  | { type: "link"; label: string; href: string }
  | { type: "dropdown"; label: string; groups: DropdownGroup[] };

// --- Data ---

const navItems: NavItem[] = [
  {
    type: "dropdown",
    label: "Resources",
    groups: [
      {
        heading: "",
        items: [
          { name: "Blog", desc: "Updates and insights", href: "/blog", icon: <FileText className="w-4 h-4" />, colors: ["#4A2A1A", "#7A4A30"] },
          { name: "Documentation", desc: "Guides and API reference", href: "/docs", icon: <FileTerminal className="w-4 h-4" />, colors: ["#135c46", "#2a8a6a"] },
          { name: "Litepaper", desc: "Protocol design and vision", href: "/litepaper", icon: <ScrollText className="w-4 h-4" />, colors: ["#1e4f7a", "#3a7ab8"] },
        ],
      },
    ],
  },
  // {
  //   type: "dropdown",
  //   label: "Product",
  //   groups: [
  //     {
  //       heading: "Tools",
  //       items: [
  //         { name: "CLI Client", desc: "Command-line trading interface", href: "/docs/clients", icon: <Terminal className="w-4 h-4" />, colors: ["#7a3318", "#a0522d"] },
  //         { name: "TUI Client", desc: "Terminal dashboard UI", href: "/docs/clients", icon: <SquareTerminal className="w-4 h-4" />, colors: ["#1e4f7a", "#3a7ab8"] },
  //         { name: "Telegram Bot", desc: "Trade from Telegram", href: "/docs/clients", icon: <Send className="w-4 h-4" />, colors: ["#4A2A1A", "#2a8a6a"] },
  //       ],
  //     },
  //   ],
  // },
  {
    type: "dropdown",
    label: "Join Us",
    groups: [
      {
        heading: "",
        items: [
          { name: "Careers", desc: "Join the team", href: "/jobs", icon: <Briefcase className="w-4 h-4" />, colors: ["#135c46", "#2a8a6a"] },
          { name: "Open Source", desc: "Contribute on GitHub", href: "https://github.com/Dragoon4002/Artic_trader", icon: <GitBranch className="w-4 h-4" />, colors: ["#4A2A1A", "#7A4A30"] },
        ],
      },
    ],
  },
];

// --- Springs ---

const springSnappy = { type: "spring" as const, stiffness: 400, damping: 28 };
const springBouncy = { type: "spring" as const, stiffness: 350, damping: 20, mass: 0.7 };

// --- PanelVisual (ghost-style) ---

function PanelVisual({ colors, icon }: { colors: [string, string]; icon: ReactNode }) {
  return (
    <motion.div
      className="w-full h-full rounded-2xl overflow-hidden relative"
      style={{ background: colors[0] }}
      initial={{ opacity: 0, scale: 0.88, rotate: -3 }}
      animate={{ opacity: 1, scale: 1, rotate: 0 }}
      exit={{ opacity: 0, scale: 0.88, rotate: 3 }}
      transition={springBouncy}
    >
      <motion.div
        className="absolute rounded-full"
        style={{ width: "70%", height: "70%", background: colors[1], right: "-10%", bottom: "-10%" }}
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 0.7 }}
        transition={{ ...springBouncy, delay: 0.04 }}
      />
      <motion.div
        className="absolute rounded-full"
        style={{ width: "45%", height: "45%", background: `${colors[1]}cc`, right: "5%", bottom: "5%" }}
        initial={{ scale: 0.3, opacity: 0 }}
        animate={{ scale: 1, opacity: 0.6 }}
        transition={{ ...springBouncy, delay: 0.08 }}
      />
      <motion.div
        className="absolute"
        style={{ width: "40%", height: "100%", background: `linear-gradient(180deg, ${colors[0]}88, ${colors[1]}44)`, left: "30%", top: 0 }}
        initial={{ opacity: 0, x: -30, scaleY: 0.8 }}
        animate={{ opacity: 0.5, x: 0, scaleY: 1 }}
        transition={{ ...springSnappy, delay: 0.06 }}
      />
      {/* Centered icon */}
      <motion.div
        className="absolute inset-0 flex items-center justify-center text-white/90 [&>svg]:w-10 [&>svg]:h-10 drop-shadow-lg"
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ ...springBouncy, delay: 0.1 }}
      >
        {icon}
      </motion.div>
    </motion.div>
  );
}

// --- Main Navbar ---

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [hoveredItem, setHoveredItem] = useState<DropdownItem | null>(null);
  const [mobileExpandedSection, setMobileExpandedSection] = useState<string | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startClose = () => {
    closeTimer.current = setTimeout(() => setActiveDropdown(null), 200);
  };
  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };

  return (
    <nav className="fixed top-4 left-0 right-0 z-50 px-4">
      <div
        className={cn(
          "max-w-5xl mx-auto px-5 h-14 flex items-center justify-between",
          "rounded-full backdrop-blur-xl",
          "bg-gradient-to-tl from-black/90 via-black/75 to-black/60",
          "border border-white/10 ring-1 ring-inset ring-white/5",
          "shadow-[0_10px_40px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_rgba(255,255,255,0.06)]"
        )}
      >
        <Logo />

        {/* Desktop nav */}
        <div
          className="hidden md:flex items-center gap-0.5"
          onMouseLeave={() => startClose()}
        >
          {navItems.map((item) => {
            if (item.type === "link") {
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className="relative px-4 py-2 text-sm font-medium text-white/60 hover:text-white transition-colors duration-150 rounded-full"
                  onMouseEnter={() => { cancelClose(); setActiveDropdown(null); }}
                >
                  <span className="relative z-10">{item.label}</span>
                </Link>
              );
            }

            const isOpen = activeDropdown === item.label;
            return (
              <div key={item.label} className="relative">
                <button
                  className={cn(
                    "relative flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-full transition-colors duration-150",
                    isOpen ? "text-white" : "text-white/60 hover:text-white"
                  )}
                  onMouseEnter={() => {
                    cancelClose();
                    setActiveDropdown(item.label);
                    setHoveredItem(item.groups[0]?.items[0] ?? null);
                  }}
                >
                  {isOpen && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 bg-white/10 rounded-full"
                      transition={springSnappy}
                    />
                  )}
                  <span className="relative z-10">{item.label}</span>
                  <ChevronDown
                    className={cn(
                      "w-3.5 h-3.5 relative z-10 transition-transform duration-200",
                      isOpen && "rotate-180"
                    )}
                  />
                </button>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.96 }}
                      transition={{ duration: 0.18, ease: [0.25, 0.1, 0.25, 1] }}
                      className="absolute top-full left-0 lg:left-1/2 lg:-translate-x-1/2 mt-3 w-[480px] flex bg-[#12121a] border border-white/[0.08] rounded-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.6)] overflow-hidden z-50"
                      onMouseEnter={cancelClose}
                      onMouseLeave={startClose}
                    >
                      <LayoutGroup id={item.label}>
                        <div className="flex-1 p-4 space-y-3 min-w-0">
                          {item.groups.map((group, gi) => (
                            <div key={group.heading || gi}>
                              {gi > 0 && <div className="h-px bg-white/5 mx-3 my-1" />}
                              {group.heading && (
                                <p className="text-[10px] uppercase tracking-wider font-semibold text-white/40 px-3 mb-1 mt-1">
                                  {group.heading}
                                </p>
                              )}
                              {group.items.map((di) => (
                                <Link
                                  key={di.name}
                                  href={di.href}
                                  className="relative block px-3 py-2.5 rounded-xl"
                                  onMouseEnter={() => setHoveredItem(di)}
                                  onClick={() => setActiveDropdown(null)}
                                >
                                  {hoveredItem?.name === di.name && (
                                    <motion.div
                                      layoutId={`highlight-${item.label}`}
                                      className="absolute inset-0 bg-white/[0.06] rounded-xl"
                                      transition={springSnappy}
                                    />
                                  )}
                                  <div className="relative z-10 min-w-0">
                                    <p className="text-sm font-medium text-white">{di.name}</p>
                                    <p className="text-xs text-white/40">{di.desc}</p>
                                  </div>
                                </Link>
                              ))}
                            </div>
                          ))}
                        </div>
                      </LayoutGroup>

                      <div className="w-[180px] p-3 shrink-0 border-l border-white/[0.06]">
                        <AnimatePresence mode="wait">
                          {hoveredItem && (
                            <PanelVisual key={hoveredItem.name} colors={hoveredItem.colors} icon={hoveredItem.icon} />
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}

          <Link
            href="/docs/quickstart"
            onMouseEnter={() => { cancelClose(); setActiveDropdown(null); }}
            className={cn(
              buttonVariants({ size: "sm" }),
              "ml-3 h-9 px-4 text-sm font-semibold rounded-2xl text-white border border-cta-border/40 bg-linear-to-b from-cta-light! to-cta! hover:from-cta! hover:to-cta-hover! transition-colors"
            )}
          >
            Launch App <ArrowRightIcon className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-white/60"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden mx-4 mt-2 rounded-2xl bg-black/90 backdrop-blur-xl border border-white/10 overflow-hidden"
          >
            <div className="p-6 space-y-2">
              {navItems.map((item) => {
                if (item.type === "link") {
                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className="block text-sm font-medium py-2 text-white/60 hover:text-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  );
                }

                const isExpanded = mobileExpandedSection === item.label;
                return (
                  <div key={item.label}>
                    <button
                      onClick={() => setMobileExpandedSection(isExpanded ? null : item.label)}
                      className="flex items-center justify-between w-full text-sm font-medium py-2 text-white/60 hover:text-white transition-colors"
                    >
                      {item.label}
                      <ChevronDown className={cn("w-4 h-4 transition-transform duration-200", isExpanded && "rotate-180")} />
                    </button>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.15 }}
                          className="overflow-hidden"
                        >
                          {item.groups.map((g, gi) => (
                            <div key={g.heading || gi} className="pl-4 mt-2">
                              {g.heading && (
                                <p className="text-[10px] uppercase text-white/30 tracking-wider mb-1 font-semibold">
                                  {g.heading}
                                </p>
                              )}
                              {g.items.map((di) => (
                                <Link
                                  key={di.name}
                                  href={di.href}
                                  onClick={() => setMobileOpen(false)}
                                  className="block py-1.5 text-sm text-white/50 hover:text-white transition-colors"
                                >
                                  {di.name}
                                </Link>
                              ))}
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}

              <Link
                href="/docs/quickstart"
                onClick={() => setMobileOpen(false)}
                className={cn(
                  buttonVariants(),
                  "block w-full text-center px-5 py-2.5 text-sm font-semibold rounded-2xl text-white border border-cta-border bg-linear-to-b from-cta-light! to-cta! hover:from-cta! hover:to-cta-hover! mt-4 transition-colors"
                )}
              >
                Launch App →
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
