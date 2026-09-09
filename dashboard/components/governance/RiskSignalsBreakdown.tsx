import { AlertTriangle, CheckCircle } from "lucide-react";

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
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 flex items-center justify-between">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-widest text-black bg-black/5 px-2 py-1 border-2 border-black">
            Current Isolation Forest Anomaly Score
          </span>
          <div className="flex items-baseline space-x-4 mt-4">
            <span
              className={`text-4xl font-bold font-mono px-3 py-1 border-2 shadow-[4px_4px_0_0_#000] ${
                (anomalyScore ?? 0) >= 0.42 ? "border-amber-500 text-amber-600 bg-[#FDFBF7]" : "border-green-500 text-green-600 bg-[#FDFBF7]"
              }`}
            >
              {anomalyScore !== null && anomalyScore !== undefined ? anomalyScore.toFixed(3) : "N/A"}
            </span>
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-black/60">
              Threshold: <span className="text-black bg-black/10 px-1">0.420</span> (FLAG trigger)
            </span>
          </div>
        </div>

        <div className="text-right">
          <span
            className={`px-4 py-2 text-xs font-bold font-mono border-2 shadow-[4px_4px_0_0_#000] inline-flex items-center space-x-2 ${
              (anomalyScore ?? 0) >= 0.42
                ? "border-amber-500 text-amber-600 bg-[#FDFBF7]"
                : "border-green-500 text-green-600 bg-[#FDFBF7]"
            }`}
          >
            {(anomalyScore ?? 0) >= 0.42 ? (
              <>
                <AlertTriangle className="w-4 h-4" />
                <span>BEHAVIORAL ANOMALY DETECTED</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>NORMAL BEHAVIOR PROFILE</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* High-Risk Signals Section */}
      {highRiskSignals.length > 0 && (
        <div className="bg-black/5 border-2 border-black p-6 shadow-[6px_6px_0_0_#000]">
          <h4 className="text-xs font-bold text-amber-500 font-mono uppercase tracking-widest mb-4 flex items-center space-x-2 bg-amber-100 border-2 border-amber-500 px-3 py-1.5 inline-flex">
            <AlertTriangle className="w-4 h-4" />
            <span>Elevated Risk Signals ({highRiskSignals.length})</span>
          </h4>
          <div className="grid grid-cols-2 gap-4">
            {highRiskSignals.map(([key, val]) => (
              <div
                key={key}
                className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-4 space-y-3"
              >
                <div className="flex items-center justify-between border-b-2 border-black/10 pb-2">
                  <span className="text-xs font-bold font-mono text-black uppercase tracking-widest">{key}</span>
                  <span className="text-xs font-bold font-mono bg-[#FDFBF7] text-amber-600 px-2 border-2 border-amber-500 shadow-[2px_2px_0_0_#000]">
                    {val.toFixed(2)}
                  </span>
                </div>
                <p className="text-[10px] text-black/60 font-bold font-mono uppercase tracking-widest">
                  {SIGNAL_DESCRIPTIONS[key] || "Canonical behavioral signal"}
                </p>
                <div className="w-full bg-black/10 border-2 border-black h-3">
                  <div
                    className="bg-amber-400 h-full border-r-2 border-black"
                    style={{ width: `${Math.min(100, Math.max(10, val * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Normal Signals Section */}
      <div className="bg-[#FDFBF7] border-2 border-black p-6 shadow-[6px_6px_0_0_#000]">
        <h4 className="text-xs font-bold text-green-600 font-mono uppercase tracking-widest mb-4 flex items-center space-x-2 bg-[#FDFBF7] border-2 border-green-500 px-3 py-1.5 inline-flex shadow-[2px_2px_0_0_#22c55e]">
          <CheckCircle className="w-4 h-4" />
          <span>Baseline Signals ({normalSignals.length})</span>
        </h4>
        <div className="grid grid-cols-3 gap-4">
          {normalSignals.map(([key, val]) => (
            <div
              key={key}
              className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-4 space-y-2 hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] transition-all"
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-widest border-b-2 border-black/10 pb-2">
                <span className="text-black/80 truncate pr-2">{key}</span>
                <span className="text-black bg-black/5 px-1 border-2 border-black">{val.toFixed(2)}</span>
              </div>
              <p className="text-[9px] text-black/50 font-bold font-mono uppercase tracking-widest truncate">
                {SIGNAL_DESCRIPTIONS[key] || "Canonical signal"}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
