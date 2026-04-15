import { Navbar } from "@/components/landing/navbar";
import { Footer } from "@/components/landing/footer";
import { DocsSidebar } from "@/components/docs/sidebar";
import { MobileDocsNav } from "@/components/docs/mobile-docs-nav";

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Navbar />
      <div className="flex flex-1 min-h-[calc(100vh-64px)] pt-16">
        <DocsSidebar />
        <div className="flex-1 flex flex-col">
          <MobileDocsNav />
          <main className="flex-1 max-w-5xl mx-auto w-full px-6 md:px-10 py-10">
            {children}
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}
