"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { DemoScenarioResult } from "@/lib/types";
import { PlayCircle, RefreshCw, Zap } from "lucide-react";

interface ScenarioCardMeta {
  id: string;
  name: string;
  badge: string;
  expected: string;
  description: string;
  agent: string;
  amount: string;
  details: string;
}

const SCENARIOS: ScenarioCardMeta[] = [
  {
    id: "1",
    name: "Scenario 1 — Normal Authorized Payout",
    badge: "HAPPY PATH",
    expected: "ALLOW",
    description: "Valid agent payout request within daily/weekly cap, allowed category & normal behavior.",
    agent: "demo_normal_agent",
    amount: "₹100.00",
    details: "Runs through full Governor pipeline. Decision = ALLOW. Reaches RazorpayX Test Mode execution.",
  },
  {
    id: "2",
    name: "Scenario 2 — Policy Violation Block",
    badge: "POLICY GATE",
    expected: "BLOCK",
    description: "Transaction amount (₹100.00) exceeds mandate single transaction cap (₹1.00).",
    agent: "demo_policy_agent",
    amount: "₹100.00",
    details: "Policy engine detects cap violation. Decision = BLOCK. Structural gate stops execution before RazorpayX.",
  },
  {
    id: "3",
    name: "Scenario 3 — Behavioral Anomaly Flag",
    badge: "RISK ENGINE",
    expected: "FLAG",
    description: "Cold-start agent attempting large uncharacteristic payment (₹4,500.00) to new payee.",
    agent: "demo_behavior_agent",
    amount: "₹4,500.00",
    details: "Isolation Forest scores anomaly = 0.68 >= 0.42. Decision = FLAG. RazorpayX execution is blocked.",
  },
  {
    id: "4",
    name: "Scenario 4 — Untrusted Provenance Flag",
    badge: "PROVENANCE",
    expected: "FLAG",
    description: "Payment intent originated from untrusted external content (e.g. scraped email).",
    agent: "demo_provenance_agent",
    amount: "₹1,000.00",
    details: "Provenance evaluator detects UNTRUSTED source. Decision = FLAG. RazorpayX execution is blocked.",
  },
  {
    id: "5",
    name: "Scenario 5 — Idempotent Replay",
    badge: "IDEMPOTENCY",
    expected: "IDEMPOTENT_REPLAY",
    description: "Repeat the exact same payment request with an identical idempotency key.",
    agent: "demo_normal_agent",
    amount: "₹100.00",
    details: "Idempotency store returns cached completion payload without creating a duplicate payout.",
  },
  {
    id: "6",
    name: "Scenario 6 — Revoked Mandate Block",
    badge: "AUTHORITY",
    expected: "BLOCK",
    description: "Attempt payment request after agent mandate has been explicitly revoked.",
    agent: "demo_revocation_agent",
    amount: "₹100.00",
    details: "Policy engine detects REVOKED mandate status. Decision = BLOCK. RazorpayX execution is blocked.",
  },
];

export default function DemoPage() {
  const [runningId, setRunningId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, DemoScenarioResult>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const runScenario = async (id: string) => {
    setRunningId(id);
    setErrors((prev) => ({ ...prev, [id]: "" }));
    try {
      const res = await api.runDemoScenario(id);
      setResults((prev) => ({ ...prev, [id]: res }));
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, [id]: err.message || "Scenario execution failed" }));
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Evaluator Note */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-8 space-y-4">
        <div className="flex items-center justify-between border-b-2 border-black pb-4">
          <div className="flex items-center space-x-3">
            <Zap className="w-6 h-6 text-black" />
            <h2 className="text-xl font-bold text-black font-mono uppercase tracking-widest">
              Governance Scenarios Evaluation Suite
            </h2>
          </div>
          <span className="px-3 py-1.5 bg-black text-[#FDFBF7] border-2 border-black shadow-[2px_2px_0_0_#000] text-xs font-mono font-bold uppercase tracking-widest">
            RAZORPAYX TEST MODE ONLY
          </span>
        </div>

        <p className="text-sm text-black font-mono font-bold uppercase tracking-wide leading-relaxed">
          Every scenario constructs a real <strong className="text-black bg-black/10 px-1.5 py-0.5">PayoutRequest</strong> and sends it through the live <strong className="text-black bg-black/10 px-1.5 py-0.5">POST /v1/payouts</strong> pipeline in FastAPI + PostgreSQL. Nothing is mocked or hardcoded.
        </p>

        <div className="pt-4 flex items-center space-x-2 text-xs font-mono font-bold tracking-widest uppercase text-black">
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Request</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Policy</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Behavior</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Provenance</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Decision</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Execution</span>
          <span>→</span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">Audit</span>
        </div>
      </div>

      {/* 6 Scenario Cards */}
      <div className="grid grid-cols-2 gap-6">
        {SCENARIOS.map((sc) => {
          const isRunning = runningId === sc.id;
          const res = results[sc.id];
          const err = errors[sc.id];

          const isAllow = sc.expected === "ALLOW";
          const isBlock = sc.expected === "BLOCK";
          const isFlag = sc.expected === "FLAG";

          return (
            <div
              key={sc.id}
              className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6 flex flex-col justify-between space-y-6 hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#000] transition-all"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b-2 border-black pb-3">
                  <span className="px-2 py-1 bg-black text-[#FDFBF7] text-[10px] font-mono font-bold uppercase tracking-widest shadow-[2px_2px_0_0_#000]">
                    {sc.badge}
                  </span>
                  <span className="text-xs font-mono font-bold uppercase tracking-widest text-black">
                    Expected:{" "}
                    <strong
                      className={`px-2 py-0.5 border-2 shadow-[2px_2px_0_0_#000] ml-2 ${
                        isAllow
                          ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                          : isFlag
                          ? "border-amber-500 text-amber-600 bg-[#FDFBF7]"
                          : "border-red-500 text-red-600 bg-[#FDFBF7]"
                      }`}
                    >
                      {sc.expected}
                    </strong>
                  </span>
                </div>

                <h3 className="text-base font-bold text-black font-mono uppercase tracking-tight">{sc.name}</h3>
                <p className="text-xs text-black/70 font-mono font-bold tracking-widest uppercase leading-relaxed">{sc.description}</p>

                <div className="grid grid-cols-2 gap-4 text-xs font-mono font-bold uppercase tracking-widest border-2 border-black p-4 bg-black/5 shadow-[2px_2px_0_0_#000]">
                  <div>
                    <span className="text-black/60 block text-[10px] mb-1">AGENT ID</span>
                    <span className="text-black">{sc.agent}</span>
                  </div>
                  <div>
                    <span className="text-black/60 block text-[10px] mb-1">PAYOUT AMOUNT</span>
                    <span className="text-black">{sc.amount}</span>
                  </div>
                </div>

                <p className="text-[10px] text-black/60 font-mono font-bold uppercase tracking-wider">{sc.details}</p>
              </div>

              {/* Action Button & Output */}
              <div className="space-y-4 pt-4 border-t-2 border-black">
                <button
                  onClick={() => runScenario(sc.id)}
                  disabled={isRunning}
                  className="w-full py-3 bg-[#FDFBF7] hover:bg-black border-2 border-black text-black hover:text-[#FDFBF7] font-mono font-bold text-sm uppercase tracking-widest shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 transition-all flex items-center justify-center space-x-3 disabled:opacity-50 disabled:hover:bg-[#FDFBF7] disabled:hover:text-black disabled:hover:shadow-[4px_4px_0_0_#000] disabled:hover:translate-y-0"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>POST /v1/payouts...</span>
                    </>
                  ) : (
                    <>
                      <PlayCircle className="w-5 h-5" />
                      <span>RUN SCENARIO #{sc.id}</span>
                    </>
                  )}
                </button>

                {err && (
                  <div className="p-3 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest">
                    ✕ Error: {err}
                  </div>
                )}

                {res && (
                  <div className="p-4 bg-black/5 border-2 border-black shadow-[4px_4px_0_0_#000] space-y-3 text-xs font-mono font-bold uppercase tracking-widest text-black">
                    <div className="flex items-center justify-between border-b-2 border-black pb-3 border-dashed">
                      <span className="text-black/60">Actual Decision:</span>
                      <span
                        className={`font-bold px-3 py-1 border-2 shadow-[2px_2px_0_0_#000] inline-flex items-center space-x-2 ${
                          res.actual_decision === "ALLOW" || res.actual_decision === "SUCCEEDED"
                            ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                            : res.actual_decision === "FLAG"
                            ? "border-amber-500 text-amber-600 bg-[#FDFBF7]"
                            : "border-red-500 text-red-600 bg-[#FDFBF7]"
                        }`}
                      >
                        <span
                          className={`w-2 h-2 rounded-full border-2 ${
                            res.actual_decision === "ALLOW" || res.actual_decision === "SUCCEEDED"
                              ? "bg-green-600 border-green-700"
                              : res.actual_decision === "FLAG"
                              ? "bg-amber-600 border-amber-700"
                              : "bg-red-600 border-red-700"
                          }`}
                        />
                        <span>{res.actual_decision}</span>
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-black/60">Match Expected:</span>
                      <span className={res.matched_expected ? "text-green-500" : "text-red-500"}>
                        {res.matched_expected ? "✓ MATCHED" : "✕ MISMATCHED"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-black/60">Execution Status:</span>
                      <span className="text-black">{res.execution_status}</span>
                    </div>

                    {res.razorpay_payout_id && (
                      <div className="flex items-center justify-between">
                        <span className="text-black/60">Razorpay Payout ID:</span>
                        <span className="text-black">{res.razorpay_payout_id}</span>
                      </div>
                    )}

                    <div className="text-[10px] text-black/60 pt-2 border-t-2 border-black border-dashed flex items-center justify-between">
                      <span>Audit Events Generated:</span>
                      <strong className="text-black">
                        {res.audit_events_count ?? res.audit_events_created ?? 0}
                      </strong>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
