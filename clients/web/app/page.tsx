import { Navbar } from "@/components/newlanding/navbar";
import { Hero } from "@/components/newlanding/hero";
import { Ticker } from "@/components/newlanding/ticker";
import { FeaturesGrid } from "@/components/newlanding/features-grid";
import { HowItWorks } from "@/components/newlanding/how-it-works";
import { ClientsSection } from "@/components/newlanding/clients-section";
import { CtaBanner } from "@/components/newlanding/cta-banner";
import { Footer } from "@/components/newlanding/footer";
import { FadeIn } from "@/components/shared/fade-in";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Ticker />
        {/* <FeatureTransition /> */}
        <FadeIn>
          <FeaturesGrid />
        </FadeIn>
        <FadeIn>
          <HowItWorks />
        </FadeIn>
        {/* <FadeIn>
          <ClientsSection />
        </FadeIn> */}
        <FadeIn>
          <CtaBanner />
        </FadeIn>
      </main>
      <Footer />
    </>
  );
}
