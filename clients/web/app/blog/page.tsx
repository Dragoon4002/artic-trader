import { Navbar } from "@/components/newlanding/navbar";
import { Footer } from "@/components/landing/footer";
import Link from "next/link";
import { ArrowRight, Clock, Calendar } from "lucide-react";

const posts = [
  {
    slug: "strategy-comparison",
    title: "A Comparative Study of Quantitative Trading Strategies",
    excerpt:
      "Deep dive into momentum, mean reversion, volatility, volume, and statistical strategies — how they work, when they shine, and how Artic's LLM selects between them.",
    date: "April 15, 2026",
    readTime: "12 min read",
    tags: ["Strategies", "Research", "Quant"],
  },
];

export default function BlogPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1 px-6 pt-32 pb-20 max-w-3xl mx-auto">
        <p className="text-xs tracking-[1.5px] uppercase text-orange-light mb-4">
          Blog
        </p>
        <h1 className="text-[clamp(28px,5vw,48px)] font-bold tracking-tight text-white mb-3">
          Insights & Updates
        </h1>
        <p className="text-lg text-white/50 max-w-md leading-relaxed mb-14">
          Insights on AI trading, quant strategies, and building Artic.
        </p>

        <div className="space-y-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group block p-6 md:p-8 rounded-[14px] border border-white/8 bg-white/3 hover:border-white/15 hover:bg-white/[0.05] transition-all duration-200"
            >
              <div className="flex flex-wrap gap-2 mb-4">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] uppercase tracking-wider font-semibold text-orange-text bg-orange/15 px-2.5 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <h2 className="text-xl md:text-2xl font-semibold text-white group-hover:text-orange-text transition-colors mb-3">
                {post.title}
              </h2>
              <p className="text-sm text-white/45 leading-relaxed mb-5">
                {post.excerpt}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-white/30">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    {post.date}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {post.readTime}
                  </span>
                </div>
                <span className="text-sm text-orange-light flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  Read <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </main>
      <Footer />
    </>
  );
}
