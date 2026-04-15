import { Navbar } from "@/components/landing/navbar";
import { Hero } from "@/components/landing/hero";
import { Ticker } from "@/components/landing/ticker";
import { FeaturesGrid } from "@/components/landing/features-grid";
import { HowItWorks } from "@/components/landing/how-it-works";
import { ClientsSection } from "@/components/landing/clients-section";
import { CtaBanner } from "@/components/landing/cta-banner";
import { Footer } from "@/components/landing/footer";
import { FadeIn } from "@/components/shared/fade-in";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Ticker />
        <FeaturesGrid />
        <FadeIn>
          <HowItWorks />
        </FadeIn>
        <FadeIn>
          <ClientsSection />
        </FadeIn>
        <FadeIn>
          <CtaBanner />
        </FadeIn>
      </main>
      <Footer />
    </>
  );
}
