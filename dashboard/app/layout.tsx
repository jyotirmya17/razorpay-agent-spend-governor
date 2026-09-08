import type { Metadata } from "next";
import "./globals.css";
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: "Agent Spend Governor — Fintech Governance Console",
  description: "Governance layer for automated agent payouts.",
};

const GRAIN_URL = "data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        <link href="https://api.fontshare.com/v2/css?f[]=general-sans@500,600,700,800&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#FDFBF7] text-[#000000] antialiased min-h-screen font-sans selection:bg-[#000000] selection:text-[#FDFBF7] relative">
        <div className="fixed inset-0 z-[9999] pointer-events-none opacity-[0.04] mix-blend-multiply" style={{ backgroundImage: `url("${GRAIN_URL}")` }}></div>
        {children}
      </body>
    </html>
  );
}
