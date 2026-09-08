import type { Metadata } from "next";
import "./globals.css";
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: "Agent Spend Governor — Fintech Governance Console",
  description: "Governance layer for automated agent payouts.",
};

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
      <body className="bg-[#FDE68A] text-[#000000] antialiased min-h-screen font-sans selection:bg-[#000000] selection:text-[#FDE68A]">
        {children}
      </body>
    </html>
  );
}
