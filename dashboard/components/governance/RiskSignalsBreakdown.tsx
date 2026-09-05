import { AlertTriangle, CheckCircle, Info } from "lucide-react";

interface RiskSignalsBreakdownProps {
  features: Record<string, number>;
  anomalyScore?: number | null;
}

const SIGNAL_DESCRIPTIONS: Record<string, string> = {
  amount_deviation: "Z-score of transaction amount vs agent historical distribution",
  payee_novelty: "Novelty indicator for new/unseen payee IDs (0.0 = known, 1.0 = unseen)",
  velocity_5m: "Transaction count in past 5-minute rolling window",
  velocity_1h: "Transaction count in past 1-hour rolling window",
  velocity_24h: "Transaction count in past 24-hour rolling window",
  time_of_day_deviation: "Hour of day deviation vs historical active hours profile",
  weekday_deviation: "Weekday deviation vs historical active days profile",
  category_deviation: "Category deviation vs preferred category distribution",
  daily_spend_deviation: "Daily total spend z-score vs historical daily spend profile",
  weekly_spend_deviation: "Weekly total spend z-score vs historical weekly spend profile",
  payee_concentration: "Concentration score for payee diversity (Herfindahl-Hirschman)",
  behavioral_distance: "Mahalanobis composite distance from centroid behavior",
};

export function RiskSignalsBreakdown({ features, anomalyScore }: RiskSignalsBreakdownProps) {
  const entries = Object.entries(features || {});
  
  // Categorize signals as high risk vs normal based on heuristic thresholds
  const highRiskSignals = entries.filter(([key, val]) => {
    if (key.includes("deviation") || key === "behavioral_distance") return val > 0.5;
    if (key === "payee_novelty") return val > 0.0;
    if (key.includes("velocity")) return val > 3;
    return false;
  });

  const normalSignals = entries.filter(([key]) => !highRiskSignals.some(([hk]) => hk === key));

  return (
    <div className="space-y-6">
      {/* Risk Score Summary Banner */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5 flex items-center justify-between">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Current Isolation Forest Anomaly Score
          </span>
          <div className="flex items-baseline space-x-3 mt-1">
            <span
              className={`text-3xl font-bold font-mono ${
                (anomalyScore ?? 0) >= 0.42 ? "text-amber-400" : "text-emerald-400"
              }`}
            >
              {anomalyScore !== null && anomalyScore !== undefined ? anomalyScore.toFixed(3) : "N/A"}
            </span>
            <span className="text-xs font-mono text-slate-400">
              Threshold: <span className="text-white font-bold">0.420</span> (FLAG trigger)
            </span>
          </div>
        </div>

        <div className="text-right">
          <span
            className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono border inline-flex items-center space-x-1.5 ${
              (anomalyScore ?? 0) >= 0.42
                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            }`}
          >
            {(anomalyScore ?? 0) >= 0.42 ? (
              <>
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>BEHAVIORAL ANOMALY DETECTED</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-3.5 h-3.5" />
                <span>NORMAL BEHAVIOR PROFILE</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* High-Risk Signals Section */}
      {highRiskSignals.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-amber-400 font-mono uppercase tracking-wider mb-3 flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Elevated Risk Signals ({highRiskSignals.length})</span>
          </h4>
          <div className="grid grid-cols-2 gap-3">
            {highRiskSignals.map(([key, val]) => (
              <div
                key={key}
                className="bg-[#171D25] border border-amber-500/30 rounded-lg p-3 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono text-white">{key}</span>
                  <span className="text-xs font-bold font-mono text-amber-400">
                    {val.toFixed(2)}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono">
                  {SIGNAL_DESCRIPTIONS[key] || "Canonical behavioral signal"}
                </p>
                <div className="w-full bg-[#0B0F14] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, Math.max(10, val * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Normal Signals Section */}
      <div>
        <h4 className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider mb-3 flex items-center space-x-1.5">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>Baseline Signals ({normalSignals.length})</span>
        </h4>
        <div className="grid grid-cols-3 gap-3">
          {normalSignals.map(([key, val]) => (
            <div
              key={key}
              className="bg-[#11161D] border border-[#232B36] rounded-lg p-3 space-y-1"
            >
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300 truncate pr-1">{key}</span>
                <span className="text-emerald-400 font-bold">{val.toFixed(2)}</span>
              </div>
              <p className="text-[9px] text-slate-500 font-mono truncate">
                {SIGNAL_DESCRIPTIONS[key] || "Canonical signal"}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
