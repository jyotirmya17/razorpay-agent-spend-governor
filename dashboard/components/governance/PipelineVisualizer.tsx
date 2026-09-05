"use client";

import { FullTransactionInvestigation } from "@/lib/types";
import { ProvenanceBadge } from "./ProvenanceBadge";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Activity,
  FileCode,
  CheckSquare,
  Lock,
  Layers,
} from "lucide-react";

interface PipelineVisualizerProps {
  data: FullTransactionInvestigation;
}

export function PipelineVisualizer({ data }: PipelineVisualizerProps) {
  const { request, policy, behavior, provenance, decision, execution } = data;

  const decVal = decision.decision;
  const isAllow = decVal === "ALLOW";
  const isBlock = decVal === "BLOCK";
  const isFlag = decVal === "FLAG";

  return (
    <div className="space-y-6">
      {/* Header Pipeline Ribbon */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
          <span className="flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-[#3395FF]" />
            <span>Governor Decision Flow Pipeline</span>
          </span>
          <span className="font-bold text-slate-300">TXN #{request.txn_id.slice(0, 16)}</span>
        </div>

        <div className="grid grid-cols-6 gap-2">
          {/* Stage 1: Request */}
          <div className="bg-[#171D25] border border-[#232B36] rounded-lg p-2.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>1. REQUEST</span>
              <FileCode className="w-3 h-3 text-[#3395FF]" />
            </div>
            <div className="mt-2">
              <p className="text-xs font-bold text-white truncate">{request.agent_id}</p>
              <p className="text-[11px] font-mono text-emerald-400 font-bold">₹{request.amount_inr}</p>
            </div>
          </div>

          {/* Stage 2: Policy */}
          <div
            className={`border rounded-lg p-2.5 flex flex-col justify-between ${
              policy.policy_allowed
                ? "bg-emerald-950/20 border-emerald-500/30"
                : "bg-red-950/20 border-red-500/30"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>2. POLICY</span>
              {policy.policy_allowed ? (
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              ) : (
                <XCircle className="w-3 h-3 text-red-400" />
              )}
            </div>
            <div className="mt-2">
              <p
                className={`text-xs font-bold font-mono ${
                  policy.policy_allowed ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {policy.policy_allowed ? "PASSED" : "VIOLATED"}
              </p>
              <p className="text-[10px] text-slate-400 truncate">
                {policy.mandate_id || "No Mandate"}
              </p>
            </div>
          </div>

          {/* Stage 3: Behavior */}
          <div
            className={`border rounded-lg p-2.5 flex flex-col justify-between ${
              (behavior.anomaly_score ?? 0) >= 0.42
                ? "bg-amber-950/20 border-amber-500/30"
                : "bg-emerald-950/20 border-emerald-500/30"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>3. BEHAVIOR</span>
              <Activity className="w-3 h-3 text-amber-400" />
            </div>
            <div className="mt-2">
              <p className="text-xs font-bold font-mono text-white">
                Score: {behavior.anomaly_score !== null ? behavior.anomaly_score?.toFixed(2) : "N/A"}
              </p>
              <p
                className={`text-[10px] font-semibold ${
                  (behavior.anomaly_score ?? 0) >= 0.42 ? "text-amber-400" : "text-emerald-400"
                }`}
              >
                {(behavior.anomaly_score ?? 0) >= 0.42 ? "ELEVATED RISK" : "NORMAL"}
              </p>
            </div>
          </div>

          {/* Stage 4: Provenance */}
          <div
            className={`border rounded-lg p-2.5 flex flex-col justify-between ${
              provenance.source_trust === "TRUSTED"
                ? "bg-emerald-950/20 border-emerald-500/30"
                : "bg-amber-950/20 border-amber-500/30"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>4. PROVENANCE</span>
              <ShieldCheck className="w-3 h-3 text-[#3395FF]" />
            </div>
            <div className="mt-2">
              <ProvenanceBadge trust={provenance.source_trust} size="sm" />
              <p className="text-[9px] text-slate-400 font-mono truncate mt-1">
                {provenance.payment_intent_origin}
              </p>
            </div>
          </div>

          {/* Stage 5: Decision */}
          <div
            className={`border rounded-lg p-2.5 flex flex-col justify-between ${
              isAllow
                ? "bg-emerald-950/30 border-emerald-500/40"
                : isFlag
                ? "bg-amber-950/30 border-amber-500/40"
                : "bg-red-950/30 border-red-500/40"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>5. DECISION</span>
              {isAllow && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
              {isFlag && <AlertTriangle className="w-3 h-3 text-amber-400" />}
              {isBlock && <XCircle className="w-3 h-3 text-red-400" />}
            </div>
            <div className="mt-2">
              <span
                className={`text-xs font-bold font-mono px-1.5 py-0.5 rounded ${
                  isAllow
                    ? "bg-emerald-500/20 text-emerald-400"
                    : isFlag
                    ? "bg-amber-500/20 text-amber-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >
                {decVal}
              </span>
            </div>
          </div>

          {/* Stage 6: Execution */}
          <div className="bg-[#171D25] border border-[#232B36] rounded-lg p-2.5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>6. EXECUTION</span>
              <CheckSquare className="w-3 h-3 text-slate-400" />
            </div>
            <div className="mt-2">
              <p className="text-xs font-bold font-mono text-white truncate">
                {execution.status}
              </p>
              <p className="text-[9px] text-slate-400 font-mono truncate">
                {execution.razorpay_payout_id || "NOT EXECUTED"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Pipeline Breakdown */}
      <div className="grid grid-cols-2 gap-4">
        {/* Left Column: Request & Policy & Provenance */}
        <div className="space-y-4">
          {/* Request Details */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider mb-3">
              1. Payout Instruction Payload
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Transaction ID</span>
                <span className="text-white font-bold">{request.txn_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Agent ID</span>
                <span className="text-[#3395FF]">{request.agent_id} ({request.agent_name})</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Amount</span>
                <span className="text-emerald-400 font-bold">₹{request.amount_inr} ({request.amount} paise)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Payee ID</span>
                <span className="text-slate-200">{request.payee_id}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Category</span>
                <span className="text-slate-200">{request.category}</span>
              </div>
            </div>
          </div>

          {/* Policy Evaluation */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider mb-3 flex items-center justify-between">
              <span>2. Deterministic Policy Mandate</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                  policy.policy_allowed ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                }`}
              >
                {policy.policy_allowed ? "PASSED" : "VIOLATED"}
              </span>
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Mandate ID</span>
                <span className="text-slate-200">{policy.mandate_id || "N/A"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Txn Cap</span>
                <span className="text-slate-200">
                  {policy.txn_cap ? `₹${(policy.txn_cap / 100).toFixed(2)}` : "Unlimited"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Daily Cap</span>
                <span className="text-slate-200">
                  {policy.daily_cap ? `₹${(policy.daily_cap / 100).toFixed(2)}` : "Unlimited"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Policy Reason</span>
                <span className={`font-bold ${policy.policy_allowed ? "text-emerald-400" : "text-red-400"}`}>
                  {policy.policy_reason || "AUTHORIZED"}
                </span>
              </div>
            </div>
          </div>

          {/* Provenance Evaluation */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider mb-3">
              4. Intent Provenance Trace
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Source Trust</span>
                <ProvenanceBadge trust={provenance.source_trust} size="sm" />
              </div>
              <div className="flex justify-between py-1 border-b border-[#232B36]">
                <span className="text-slate-400">Origin Type</span>
                <span className="text-slate-200">{provenance.source_type}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Origin ID</span>
                <span className="text-slate-300">{provenance.source_id}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Behavioral & Decision & Execution & Audit */}
        <div className="space-y-4">
          {/* Behavioral Anomaly Evaluation */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider mb-3 flex items-center justify-between">
              <span>3. Behavioral Anomaly Model</span>
              <span className="text-[10px] text-slate-400 font-mono">{behavior.model_version}</span>
            </h3>
            <div className="mb-4 bg-[#171D25] border border-[#232B36] p-3 rounded-lg flex items-center justify-between">
              <div>
                <p className="text-[10px] text-slate-400 font-mono">Isolation Forest Score</p>
                <p
                  className={`text-xl font-bold font-mono ${
                    (behavior.anomaly_score ?? 0) >= 0.42 ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {behavior.anomaly_score !== null ? behavior.anomaly_score?.toFixed(3) : "N/A"}
                </p>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-slate-400 font-mono">Flag Threshold</p>
                <p className="text-xs font-mono text-slate-300 font-bold">0.420</p>
              </div>
            </div>

            {/* Feature Signals summary */}
            <div className="space-y-1.5">
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-2">
                Evaluated Behavioral Features
              </p>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono">
                {Object.entries(behavior.canonical_features || {}).map(([key, val]) => (
                  <div key={key} className="bg-[#171D25] px-2 py-1 rounded border border-[#232B36] flex justify-between">
                    <span className="text-slate-400 truncate pr-1">{key}</span>
                    <span className="text-slate-200 font-bold">{val.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Governor Final Decision */}
          <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider mb-3">
              5 & 6. Governor Decision & Execution Gate
            </h3>
            <div className="p-3 bg-[#171D25] rounded-lg border border-[#232B36] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">Final Risk Decision:</span>
                <span
                  className={`px-3 py-1 rounded text-sm font-bold font-mono ${
                    isAllow
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : isFlag
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      : "bg-red-500/20 text-red-400 border border-red-500/30"
                  }`}
                >
                  {decVal}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">RazorpayX Payout Gate:</span>
                <span className="font-bold text-white">
                  {execution.razorpay_payout_id ? (
                    <span className="text-emerald-400">EXECUTED ({execution.razorpay_payout_id})</span>
                  ) : (
                    <span className="text-slate-400">NEVER EXECUTED (GATE CLOSED)</span>
                  )}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                  Aggregated Reason Codes
                </span>
                <div className="flex flex-wrap gap-1">
                  {decision.reason_codes.map((rc, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-[#0B0F14] border border-[#232B36] rounded text-[10px] font-mono text-slate-300">
                      {rc}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
