"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { RiskOverview } from "@/lib/types";
import { RiskSignalsBreakdown } from "@/components/governance/RiskSignalsBreakdown";
import { AlertTriangle, ShieldCheck, Activity, Layers, PieChart } from "lucide-react";

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
    <div className="space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-tight">
            Risk & Anomaly Command Center
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Operational risk distribution, score histogram & 12 canonical feature signals
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-[#11161D] px-3 py-1.5 rounded-lg border border-[#232B36]">
          Model: <strong className="text-[#3395FF]">behavioral_iforest_v1</strong>
        </span>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          <div className="animate-pulse bg-[#11161D] h-32 rounded-xl border border-[#232B36]" />
          <div className="animate-pulse bg-[#11161D] h-64 rounded-xl border border-[#232B36]" />
        </div>
      ) : (
        <>
          {/* Anomaly Score Bucket Cards */}
          <div className="grid grid-cols-4 gap-4 font-mono">
            <div className="bg-[#11161D] border border-emerald-500/20 rounded-xl p-4">
              <span className="text-xs text-slate-400 block">LOW RISK (&lt; 0.30)</span>
              <p className="text-2xl font-bold text-emerald-400 mt-1 tabular-nums">
                {riskData?.score_buckets?.low_risk_lt_03 || 0}
              </p>
              <span className="text-[10px] text-slate-500 block mt-1">Normal baseline behavior</span>
            </div>

            <div className="bg-[#11161D] border border-blue-500/20 rounded-xl p-4">
              <span className="text-xs text-slate-400 block">MODERATE (0.30 - 0.50)</span>
              <p className="text-2xl font-bold text-[#3395FF] mt-1 tabular-nums">
                {riskData?.score_buckets?.moderate_03_05 || 0}
              </p>
              <span className="text-[10px] text-slate-500 block mt-1">Near threshold zone</span>
            </div>

            <div className="bg-[#11161D] border border-amber-500/20 rounded-xl p-4">
              <span className="text-xs text-slate-400 block">ELEVATED (0.50 - 0.70)</span>
              <p className="text-2xl font-bold text-amber-400 mt-1 tabular-nums">
                {riskData?.score_buckets?.elevated_05_07 || 0}
              </p>
              <span className="text-[10px] text-slate-500 block mt-1">Flagged for review</span>
            </div>

            <div className="bg-[#11161D] border border-red-500/20 rounded-xl p-4">
              <span className="text-xs text-slate-400 block">HIGH RISK (&ge; 0.70)</span>
              <p className="text-2xl font-bold text-red-400 mt-1 tabular-nums">
                {riskData?.score_buckets?.high_risk_gte_07 || 0}
              </p>
              <span className="text-[10px] text-slate-500 block mt-1">High anomaly deviation</span>
            </div>
          </div>

          {/* Reason Code Frequencies */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5 space-y-4">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center space-x-2">
              <Activity className="w-4 h-4 text-[#3395FF]" />
              <span>Operational Risk Reason Code Frequency</span>
            </h3>

            {riskData?.reason_code_frequencies?.length === 0 ? (
              <p className="text-xs font-mono text-slate-500">No risk reason codes logged yet.</p>
            ) : (
              <div className="space-y-2 font-mono text-xs">
                {riskData?.reason_code_frequencies.map((item) => (
                  <div
                    key={item.reason}
                    className="bg-[#171D25] border border-[#232B36] p-3 rounded-lg flex items-center justify-between"
                  >
                    <span className="text-white font-bold">{item.reason}</span>
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-400 text-[10px]">Occurrences:</span>
                      <span className="px-2 py-0.5 rounded bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20 font-bold">
                        {item.count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Canonical 12 Behavioral Signals Reference */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center space-x-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                <span>12 Canonical Behavioral Risk Feature Schema</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-400">Phase 4.2 Feature Definition</span>
            </div>

            <RiskSignalsBreakdown features={dummyFeaturesSample} anomalyScore={0.18} />
          </div>
        </>
      )}
    </div>
  );
}
