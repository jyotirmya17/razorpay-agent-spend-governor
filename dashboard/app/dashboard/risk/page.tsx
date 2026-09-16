"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { RiskOverview } from "@/lib/types";
import { RiskSignalsBreakdown } from "@/components/governance/RiskSignalsBreakdown";
import { Activity, Layers } from "lucide-react";

export default function RiskPage() {
  const [riskData, setRiskData] = useState<RiskOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRisk = async () => {
    try {
      setError(null);
      const data = await api.getRiskOverview();
      setRiskData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load operational risk overview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRisk();
    window.addEventListener("governor_refresh", fetchRisk);
    return () => window.removeEventListener("governor_refresh", fetchRisk);
  }, []);

  const dummyFeaturesSample = {
    amount_deviation: 0.12,
    payee_novelty: 0.0,
    velocity_5m: 0.0,
    velocity_1h: 1.0,
    velocity_24h: 3.0,
    time_of_day_deviation: 0.05,
    weekday_deviation: 0.1,
    category_deviation: 0.0,
    daily_spend_deviation: 0.15,
    weekly_spend_deviation: 0.22,
    payee_concentration: 0.85,
    behavioral_distance: 0.18,
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h2 className="text-xl font-bold text-black font-mono tracking-tight uppercase">
            Risk & Anomaly Command Center
          </h2>
          <p className="text-xs text-black/60 font-mono mt-1 font-bold tracking-widest uppercase">
            Operational risk distribution & 12 feature signals
          </p>
        </div>
        <span className="text-xs font-mono font-bold tracking-widest text-black bg-[#FDFBF7] px-4 py-2 border-2 border-black shadow-[4px_4px_0_0_#000] uppercase">
          Model: <strong className="text-black ml-2 underline underline-offset-4 decoration-black/30">behavioral_iforest_v1</strong>
        </span>
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest flex items-center space-x-2">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-6">
          <div className="animate-pulse bg-[#FDFBF7] h-32 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          <div className="animate-pulse bg-[#FDFBF7] h-64 border-2 border-black shadow-[4px_4px_0_0_#000]" />
        </div>
      ) : (
        <>
          {/* Anomaly Score Bucket Cards */}
          <div className="grid grid-cols-4 gap-6 font-mono font-bold uppercase tracking-widest text-black">
            <div className="bg-[#FDFBF7] border-2 border-green-500 shadow-[6px_6px_0_0_#22c55e] p-5 hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#22c55e] transition-all">
              <span className="text-[10px] text-green-600 border-b-2 border-green-500 pb-1 block">LOW RISK (&lt; 0.30)</span>
              <p className="text-4xl font-bold text-black mt-3 tabular-nums">
                {riskData?.score_buckets?.low_risk_lt_03 || 0}
              </p>
              <span className="text-[10px] text-black/70 block mt-2 leading-tight bg-black/5 px-2 py-1">Normal baseline behavior</span>
            </div>

            <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-5 hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#000] transition-all">
              <span className="text-[10px] text-black border-b-2 border-black pb-1 block">MODERATE (0.30 - 0.50)</span>
              <p className="text-4xl font-bold text-black mt-3 tabular-nums">
                {riskData?.score_buckets?.moderate_03_05 || 0}
              </p>
              <span className="text-[10px] text-black/60 block mt-2 leading-tight bg-black/5 px-2 py-1">Near threshold zone</span>
            </div>

            <div className="bg-[#FDFBF7] border-2 border-amber-500 shadow-[6px_6px_0_0_#f59e0b] p-5 hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#f59e0b] transition-all">
              <span className="text-[10px] text-amber-600 border-b-2 border-amber-500 pb-1 block">ELEVATED (0.50 - 0.70)</span>
              <p className="text-4xl font-bold text-black mt-3 tabular-nums">
                {riskData?.score_buckets?.elevated_05_07 || 0}
              </p>
              <span className="text-[10px] text-black/70 block mt-2 leading-tight bg-black/5 px-2 py-1">Review required</span>
            </div>

            <div className="bg-[#FDFBF7] border-2 border-red-500 shadow-[6px_6px_0_0_#ef4444] p-5 hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#ef4444] transition-all text-black">
              <span className="text-[10px] text-red-600 border-b-2 border-red-500 pb-1 block">HIGH RISK (&ge; 0.70)</span>
              <p className="text-4xl font-bold mt-3 tabular-nums">
                {riskData?.score_buckets?.high_risk_gte_07 || 0}
              </p>
              <span className="text-[10px] block mt-2 leading-tight bg-black/10 px-2 py-1">High anomaly deviation</span>
            </div>
          </div>

          {/* Reason Code Frequencies */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 space-y-6">
            <h3 className="text-sm font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2 border-b-2 border-black pb-4">
              <Activity className="w-5 h-5" />
              <span>Operational Risk Reason Code Frequency</span>
            </h3>

            {riskData?.reason_code_frequencies?.length === 0 ? (
              <p className="text-xs font-mono font-bold uppercase tracking-widest text-black/50 border-2 border-dashed border-black p-8 text-center">No risk reason codes logged yet.</p>
            ) : (
              <div className="space-y-4 font-mono text-xs font-bold uppercase tracking-widest">
                {riskData?.reason_code_frequencies.map((item) => (
                  <div
                    key={item.reason}
                    className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-4 flex items-center justify-between"
                  >
                    <span className="text-black">{item.reason}</span>
                    <div className="flex items-center space-x-4">
                      <span className="text-black/60 text-[10px]">Occurrences:</span>
                      <span className="px-3 py-1 bg-black text-[#FDFBF7] border-2 border-black shadow-[2px_2px_0_0_#000]">
                        {item.count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Canonical 12 Behavioral Signals Reference */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 space-y-6">
            <div className="flex items-center justify-between border-b-2 border-black pb-4">
              <h3 className="text-sm font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2">
                <Layers className="w-5 h-5" />
                <span>12 Canonical Behavioral Risk Feature Schema</span>
              </h3>
              <span className="text-[10px] font-mono font-bold bg-black text-[#FDFBF7] px-3 py-1 uppercase tracking-widest shadow-[2px_2px_0_0_#000]">
                Phase 4.2 Feature Definition
              </span>
            </div>

            <RiskSignalsBreakdown features={dummyFeaturesSample} anomalyScore={0.18} />
          </div>
        </>
      )}
    </div>
  );
}
