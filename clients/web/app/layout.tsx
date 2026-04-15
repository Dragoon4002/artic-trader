import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Artic — AI-Powered Multi-Agent Trading",
  description:
    "Deploy AI trading agents on any market at any scale. Artic is the orchestration hub for AI-powered trading with 30+ quant strategies.",
  icons: {
    icon: "/artic-logo.png",
  },
  keywords: [
    "AI trading",
    "quantitative trading",
    "algorithmic trading",
    "multi-agent systems",
    "crypto trading",
    "stock trading",
    "forex trading",
    "trading bots",
  ],
  authors: [{ name: "Silonelabs" }],
  openGraph: {
    title: "Artic — AI-Powered Multi-Agent Trading",
    description:
      "Deploy AI trading agents on any market at any scale. Artic is the orchestration hub for AI-powered trading with 30+ quant strategies.",
    images: [
      {
        url: "/artic-logo.png",
        width: 800,
        height: 600,
        alt: "Artic Logo",
      },
    ],
    siteName: "Artic",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${geistMono.variable} dark antialiased`}
    >
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
