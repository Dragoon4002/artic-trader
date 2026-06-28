"use client";

import dynamic from "next/dynamic";
import { Navbar } from "@/components/newlanding/navbar";
import { LandingSnapContainer } from "@/components/newlanding/landing-snap-container";
import { LandingThemeProvider, useLandingTheme } from "@/components/newlanding/theme-context";
import { Hero } from "@/components/newlanding/hero";

function SectionFallback() {
  return <div className="min-h-screen w-full bg-background" aria-hidden />;
}

const FeaturesBento = dynamic(
  () => import("@/components/newlanding/features-bento").then((m) => m.FeaturesBento),
  { loading: SectionFallback }
);
const StrategyCatalog = dynamic(
  () => import("@/components/newlanding/strategy-catalog").then((m) => m.StrategyCatalog),
  { loading: SectionFallback }
);
const HowItWorksSection = dynamic(
  () => import("@/components/newlanding/how-it-works-single").then((m) => m.HowItWorksSection),
  { loading: SectionFallback }
);
const LlmMatrix = dynamic(
  () => import("@/components/newlanding/llm-matrix").then((m) => m.LlmMatrix),
  { loading: SectionFallback }
);
const OnchainProof = dynamic(
  () => import("@/components/newlanding/onchain-proof").then((m) => m.OnchainProof),
  { loading: SectionFallback }
);
const LivePnlFeed = dynamic(
  () => import("@/components/newlanding/live-pnl-feed").then((m) => m.LivePnlFeed),
  { loading: SectionFallback }
);
const Faq = dynamic(
  () => import("@/components/newlanding/faq").then((m) => m.Faq),
  { loading: SectionFallback }
);
const Waitlist = dynamic(
  () => import("@/components/newlanding/waitlist").then((m) => m.Waitlist),
  { loading: SectionFallback }
);
const CtaBanner = dynamic(
  () => import("@/components/newlanding/cta-banner").then((m) => m.CtaBanner),
  { loading: SectionFallback }
);
const Footer = dynamic(
  () => import("@/components/newlanding/footer").then((m) => m.Footer),
  { loading: SectionFallback }
);

function LandingShell() {
  const ctx = useLandingTheme();
  const isLight = ctx?.theme === "light";

  return (
    <div className={isLight ? "landing-light" : ""}>
      <div className="bg-background text-foreground">
        <Navbar />
        <LandingSnapContainer
          top={[<Hero key="hero" />]}
          middle={[
            <FeaturesBento key="bento" />,
            <StrategyCatalog key="strat" />,
            <HowItWorksSection key="hiw" />,
            <LlmMatrix key="llm" />,
            <OnchainProof key="oc" />,
            <LivePnlFeed key="pnl" />,
          ]}
          bottom={[
            <Faq key="faq" />,
            <Waitlist key="wait" />,
            <CtaBanner key="cta" />,
            <Footer key="foot" />,
          ]}
        />
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <LandingThemeProvider>
      <LandingShell />
    </LandingThemeProvider>
  );
}