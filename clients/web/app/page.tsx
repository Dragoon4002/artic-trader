"use client";

import { Navbar } from "@/components/newlanding/navbar";
import { HeroArctic } from "@/components/newlanding/hero-arctic";
import { FeaturesBento } from "@/components/newlanding/features-bento";
import { StrategyCatalog } from "@/components/newlanding/strategy-catalog";
import { HowItWorksSection } from "@/components/newlanding/how-it-works-single";
import { LlmMatrix } from "@/components/newlanding/llm-matrix";
import { OnchainProof } from "@/components/newlanding/onchain-proof";
import { LivePnlFeed } from "@/components/newlanding/live-pnl-feed";
import { Faq } from "@/components/newlanding/faq";
import { Waitlist } from "@/components/newlanding/waitlist";
import { CtaBanner } from "@/components/newlanding/cta-banner";
import { Footer } from "@/components/newlanding/footer";
import { LandingSnapContainer } from "@/components/newlanding/landing-snap-container";
import { LandingThemeProvider, useLandingTheme } from "@/components/newlanding/theme-context";
import { Hero } from "@/components/newlanding/hero";

function LandingShell() {
  const ctx = useLandingTheme();
  const isLight = ctx?.theme === "light";

  return (
    <div className={isLight ? "landing-light" : ""}>
      <div className="bg-background text-foreground">
        <Navbar />
        <LandingSnapContainer
          top={[Hero ? <Hero key="hero" /> : <HeroArctic key="hero" />]}
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
