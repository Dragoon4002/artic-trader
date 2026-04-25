import { Navbar } from "@/components/newlanding/navbar";
import { Hero } from "@/components/newlanding/hero";
import { Ticker } from "@/components/newlanding/ticker";
import { FeaturesGrid } from "@/components/newlanding/features-grid";
import { HowItWorks } from "@/components/newlanding/how-it-works";
import { ClientsSection } from "@/components/newlanding/clients-section";
import { CtaBanner } from "@/components/newlanding/cta-banner";
import { Footer } from "@/components/newlanding/footer";
import { FeatureTransition } from "@/components/newlanding/feature-transition";
import { ButtonLab } from "@/components/newlanding/button-lab";
import { FadeIn } from "@/components/shared/fade-in";

const INK = "#0E141A";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Ticker />
        {/* <FeatureTransition /> */}
        <FeaturesGrid />
        <FadeIn>
          <HowItWorks />
        </FadeIn>
        <FadeIn>
          <ClientsSection />
        </FadeIn>
        <FadeIn>
          <ButtonLab />
        </FadeIn>
        <FadeIn>
          <CtaBanner />
        </FadeIn>
      </main>
      <Footer />
      {/* Giant wordmark */}
      {/* <div className="max-w-screen relative overflow-hidden bg-[#CCD2D6] h-80">
        <h3
          aria-hidden
          className="font-bold tracking-tighter leading-[0.85] select-none whitespace-nowrap text-center bg-clip-text text-transparent"
          style={{
            fontSize: "clamp(196px, 44vw, 620px)",
            backgroundImage: `linear-gradient(180deg, rgba(14,20,26,0.05) 0%, ${INK} 100%)`,
          }}
        >
          ARTIC
        </h3>
      </div> */}
    </>
  );
}
