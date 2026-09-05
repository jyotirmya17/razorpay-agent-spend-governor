"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { ShieldCheck, RefreshCw, Cpu } from "lucide-react";
import { api } from "@/lib/api";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Overview",
    subtitle: "Real-time AI-agent payout defense console",
  },
  "/agents": {
    title: "Agents & Authority",
    subtitle: "Active agent profiles, mandates & spend limits",
  },
  "/mandates": {
    title: "Mandate Policies",
    subtitle: "Policy rules, daily/weekly caps & revocation control",
  },
  "/transactions": {
    title: "Transactions",
    subtitle: "High-density decision pipeline investigation log",
  },
  "/risk": {
    title: "Risk Command Center",
    subtitle: "Isolation Forest anomaly scores & 12 feature signals",
  },
  "/audit": {
    title: "Audit Trail",
    subtitle: "Cryptographic SHA-256 tamper-evident event log",
  },
  "/demo": {
    title: "Demo Center",
    subtitle: "Interactive evaluator scenario test suite",
  },
};

export function Header() {
  const pathname = usePathname();
  const [lastSync, setLastSync] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pageInfo = PAGE_TITLES[pathname] || {
    title: "Governor Dashboard",
    subtitle: "Defense layer for autonomous AI-agent payouts",
  };

  const updateTimestamp = () => {
    setLastSync(new Date().toLocaleTimeString());
  };

  useEffect(() => {
    updateTimestamp();
    const interval = setInterval(updateTimestamp, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    updateTimestamp();
    window.dispatchEvent(new CustomEvent("governor_refresh"));
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <header className="h-16 border-b border-[#232B36] bg-[#11161D]/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
          <span>{pageInfo.title}</span>
        </h1>
        <p className="text-[11px] text-slate-400 font-normal">
          {pageInfo.subtitle}
        </p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Environment Badge */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#171D25] border border-[#232B36] text-[11px]">
          <Cpu className="w-3.5 h-3.5 text-[#3395FF]" />
          <span className="text-slate-300 font-medium">Mode:</span>
          <span className="font-mono text-emerald-400 font-bold">TEST_MODE</span>
        </div>

        {/* Sync Indicator */}
        <button
          onClick={handleManualRefresh}
          className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#171D25] hover:bg-[#232B36] border border-[#232B36] text-[11px] text-slate-300 transition-colors"
          title="Refresh Data"
        >
          <RefreshCw className={`w-3 h-3 text-slate-400 ${isRefreshing ? "animate-spin" : ""}`} />
          <span className="font-mono text-slate-400 text-[10px]">
            {lastSync ? `Sync ${lastSync}` : "Syncing..."}
          </span>
        </button>

        {/* Status Security Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Governor Active</span>
        </div>
      </div>
    </header>
  );
}
