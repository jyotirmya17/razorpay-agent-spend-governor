"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { ShieldCheck, RefreshCw, Cpu } from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": {
    title: "Overview",
    subtitle: "Real-time agent payout governance console",
  },
  "/dashboard/agents": {
    title: "Agents & Authority",
    subtitle: "Active agent profiles, mandates & spend limits",
  },
  "/dashboard/mandates": {
    title: "Mandate Policies",
    subtitle: "Policy rules, daily/weekly caps & revocation control",
  },
  "/dashboard/transactions": {
    title: "Transactions",
    subtitle: "Decision pipeline investigation log",
  },
  "/dashboard/risk": {
    title: "Risk Command Center",
    subtitle: "Isolation Forest anomaly scores & feature signals",
  },
  "/dashboard/audit": {
    title: "Audit Trail",
    subtitle: "Cryptographic SHA-256 tamper-evident event log",
  },
  "/dashboard/demo": {
    title: "Governance Scenarios",
    subtitle: "Interactive evaluator scenario test suite",
  },
};

export function Header() {
  const pathname = usePathname();
  const [lastSync, setLastSync] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pageInfo = PAGE_TITLES[pathname] || {
    title: "Governor Dashboard",
    subtitle: "Governance layer for automated agent payouts",
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
    <header className="h-20 border-b-2 border-black bg-[#FDFBF7] px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-2xl font-bold text-black tracking-tight uppercase font-mono">
          {pageInfo.title}
        </h1>
        <p className="text-[11px] text-black/60 font-bold font-mono tracking-widest uppercase mt-1">
          {pageInfo.subtitle}
        </p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Environment Badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 border-2 border-black bg-black text-[#FDFBF7] shadow-[2px_2px_0_0_#000] text-[10px] font-mono font-bold tracking-widest uppercase">
          <Cpu className="w-3.5 h-3.5 text-[#FDFBF7]" />
          <span>Mode: TEST_MODE</span>
        </div>

        {/* Sync Indicator */}
        <button
          onClick={handleManualRefresh}
          className="flex items-center space-x-2 px-3 py-1.5 border-2 border-black bg-[#FDFBF7] text-black hover:bg-black hover:text-[#FDFBF7] shadow-[2px_2px_0_0_#000] text-[10px] font-mono font-bold tracking-widest uppercase transition-colors"
          title="Refresh Data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          <span>
            {lastSync ? `Sync ${lastSync}` : "Syncing..."}
          </span>
        </button>

        {/* Status Security Badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 border-2 border-green-500 bg-[#FDFBF7] text-green-600 shadow-[2px_2px_0_0_#22c55e] text-[10px] font-mono font-bold tracking-widest uppercase">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Governor Active</span>
        </div>
      </div>
    </header>
  );
}
