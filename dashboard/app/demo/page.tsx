"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { DemoScenarioResult } from "@/lib/types";
import {
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Shield,
  Zap,
  ArrowRight,
  Layers,
} from "lucide-react";

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
    <div className="space-y-6 font-sans">
      {/* Header & Evaluator Note */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Zap className="w-5 h-5 text-[#3395FF]" />
            <h2 className="text-lg font-bold text-white font-mono uppercase tracking-wider">
              Evaluator Interactive Demo Suite
            </h2>
          </div>
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono font-bold">
            RAZORPAYX TEST MODE ONLY
          </span>
        </div>

        <p className="text-xs text-slate-300 font-mono leading-relaxed">
          Every scenario constructs a real <strong className="text-white">PayoutRequest</strong> and sends it through the live <strong className="text-[#3395FF]">POST /v1/payouts</strong> pipeline in FastAPI + PostgreSQL. Nothing is mocked or hardcoded.
        </p>

        <div className="pt-2 flex items-center space-x-4 text-[11px] font-mono text-slate-400 border-t border-[#232B36]">
          <span>Request → Policy → Behavior → Provenance → Decision → Execution → Audit</span>
        </div>
      </div>

      {/* 6 Scenario Cards */}
      <div className="grid grid-cols-2 gap-4">
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
              className="bg-[#11161D] border border-[#232B36] hover:border-[#3395FF]/40 transition-colors rounded-xl p-5 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20 text-[10px] font-mono font-bold">
                    {sc.badge}
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    Expected:{" "}
                    <strong
                      className={
                        isAllow
                          ? "text-emerald-400"
                          : isFlag
                          ? "text-amber-400"
                          : "text-red-400"
                      }
                    >
                      {sc.expected}
                    </strong>
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white font-mono">{sc.name}</h3>
                <p className="text-xs text-slate-300 font-mono leading-relaxed">{sc.description}</p>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-[#171D25] p-2.5 rounded-lg border border-[#232B36]">
                  <div>
                    <span className="text-slate-500 block text-[9px]">AGENT ID</span>
                    <span className="text-white font-bold">{sc.agent}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px]">PAYOUT AMOUNT</span>
                    <span className="text-emerald-400 font-bold">{sc.amount}</span>
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 font-mono italic">{sc.details}</p>
              </div>

              {/* Action Button & Output */}
              <div className="space-y-3 pt-2 border-t border-[#232B36]">
                <button
                  onClick={() => runScenario(sc.id)}
                  disabled={isRunning}
                  className="w-full py-2 bg-[#171D25] hover:bg-[#232B36] border border-[#3395FF]/40 text-[#3395FF] hover:text-white font-mono font-bold text-xs rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Orchestrating POST /v1/payouts...</span>
                    </>
                  ) : (
                    <>
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>RUN SCENARIO #{sc.id}</span>
                    </>
                  )}
                </button>

                {err && (
                  <div className="p-2.5 bg-red-500/10 border border-red-500/20 rounded text-[11px] font-mono text-red-400">
                    ✕ Error: {err}
                  </div>
                )}

                {res && (
                  <div className="p-3 bg-[#171D25] border border-[#232B36] rounded-lg space-y-2 text-xs font-mono">
                    <div className="flex items-center justify-between border-b border-[#232B36] pb-2">
                      <span className="text-slate-400">Actual Decision:</span>
                      <span
                        className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                          res.actual_decision === "ALLOW"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : res.actual_decision === "FLAG"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-red-500/10 text-red-400 border border-red-500/20"
                        }`}
                      >
                        {res.actual_decision}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Match Expected:</span>
                      <span className={res.matched_expected ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                        {res.matched_expected ? "✓ MATCHED" : "✕ MISMATCHED"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Execution Status:</span>
                      <span className="text-white font-bold">{res.execution_status}</span>
                    </div>

                    {res.razorpay_payout_id && (
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400">Razorpay Payout ID:</span>
                        <span className="text-emerald-400 font-bold">{res.razorpay_payout_id}</span>
                      </div>
                    )}

                    <div className="text-[10px] text-slate-400 pt-1 border-t border-[#232B36]">
                      <span>Audit Events Generated: <strong className="text-white">{res.audit_events_created}</strong></span>
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
