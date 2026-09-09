"use client";

import { FullTransactionInvestigation } from "@/lib/types";
import { ProvenanceBadge } from "./ProvenanceBadge";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  Activity,
  FileCode,
  CheckSquare,
  Layers,
} from "lucide-react";

interface PipelineVisualizerProps {
  data: FullTransactionInvestigation;
}

export function PipelineVisualizer({ data }: PipelineVisualizerProps) {
  const { request, policy, behavior, provenance, decision, execution } = data;

  const decVal = decision.decision;
  const isAllow = decVal === "ALLOW" || decVal === "SUCCEEDED";
  const isBlock = decVal === "BLOCK";
  const isFlag = decVal === "FLAG";

  return (
    <div className="space-y-6">
      {/* Header Pipeline Ribbon */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6">
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-black mb-6 flex items-center justify-between border-b-2 border-black pb-4">
          <span className="flex items-center space-x-2">
            <Layers className="w-5 h-5" />
            <span className="bg-black text-[#FDFBF7] px-2 py-1 border-2 border-black">Governor Decision Flow Pipeline</span>
          </span>
          <span className="bg-black/5 px-2 py-1 border-2 border-black">TXN #{request.txn_id.slice(0, 16)}</span>
        </div>

        <div className="grid grid-cols-6 gap-4">
          {/* Stage 1: Request */}
          <div className="bg-black/5 border-2 border-black shadow-[4px_4px_0_0_#000] p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000]">
            <div className="flex items-center justify-between text-[10px] text-black font-bold font-mono uppercase tracking-widest border-b-2 border-black/10 pb-2">
              <span>1. REQUEST</span>
              <FileCode className="w-4 h-4" />
            </div>
            <div className="mt-4">
              <p className="text-xs font-bold text-black truncate">{request.agent_id}</p>
              <p className="text-[11px] font-mono text-black font-bold mt-1 bg-black/5 inline-block px-1">₹{request.amount_inr}</p>
            </div>
          </div>

          {/* Stage 2: Policy */}
          <div
            className={`bg-[#FDFBF7] border-2 border-black p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] ${
              policy.policy_allowed
                ? "shadow-[4px_4px_0_0_#4ade80]"
                : "shadow-[4px_4px_0_0_#ef4444]"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-bold font-mono uppercase tracking-widest border-b-2 border-black/10 pb-2 text-black">
              <span>2. POLICY</span>
              {policy.policy_allowed ? (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
            </div>
            <div className="mt-4">
              <p className={`text-xs font-bold font-mono uppercase tracking-widest ${policy.policy_allowed ? "text-green-600" : "text-red-600"}`}>
                {policy.policy_allowed ? "PASSED" : "VIOLATED"}
              </p>
              <p className="text-[10px] font-bold mt-1 truncate text-black/70">
                {policy.mandate_id || "No Mandate"}
              </p>
            </div>
          </div>

          {/* Stage 3: Behavior */}
          <div
            className={`bg-[#FDFBF7] border-2 border-black p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] ${
              (behavior.anomaly_score ?? 0) >= 0.42
                ? "shadow-[4px_4px_0_0_#fbbf24]"
                : "shadow-[4px_4px_0_0_#4ade80]"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-bold text-black font-mono uppercase tracking-widest border-b-2 border-black/10 pb-2">
              <span>3. BEHAVIOR</span>
              <Activity className={`w-4 h-4 ${(behavior.anomaly_score ?? 0) >= 0.42 ? "text-amber-500" : "text-green-500"}`} />
            </div>
            <div className="mt-4">
              <p className="text-xs font-bold font-mono text-black">
                Score: {behavior.anomaly_score !== null ? behavior.anomaly_score?.toFixed(2) : "N/A"}
              </p>
              <p className={`text-[10px] font-bold mt-1 uppercase tracking-widest ${(behavior.anomaly_score ?? 0) >= 0.42 ? "text-amber-600" : "text-green-600"}`}>
                {(behavior.anomaly_score ?? 0) >= 0.42 ? "ELEVATED RISK" : "NORMAL"}
              </p>
            </div>
          </div>

          {/* Stage 4: Provenance */}
          <div
            className={`bg-[#FDFBF7] border-2 border-black p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] ${
              provenance.source_trust === "TRUSTED"
                ? "shadow-[4px_4px_0_0_#4ade80]"
                : "shadow-[4px_4px_0_0_#fbbf24]"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-bold text-black font-mono uppercase tracking-widest border-b-2 border-black/10 pb-2">
              <span>4. PROVENANCE</span>
              <ShieldCheck className={`w-4 h-4 ${provenance.source_trust === "TRUSTED" ? "text-green-500" : "text-amber-500"}`} />
            </div>
            <div className="mt-4">
              <ProvenanceBadge trust={provenance.source_trust} size="sm" />
              <p className="text-[9px] text-black/80 font-bold font-mono truncate mt-2">
                {provenance.payment_intent_origin}
              </p>
            </div>
          </div>

          {/* Stage 5: Decision */}
          <div
            className={`bg-[#FDFBF7] border-2 border-black p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] ${
              isAllow
                ? "shadow-[4px_4px_0_0_#4ade80]"
                : isFlag
                ? "shadow-[4px_4px_0_0_#fbbf24]"
                : "shadow-[4px_4px_0_0_#ef4444]"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-bold font-mono uppercase tracking-widest border-b-2 border-black/10 pb-2 text-black">
              <span>5. DECISION</span>
              {isAllow && <CheckCircle2 className="w-4 h-4 text-green-500" />}
              {isFlag && <AlertTriangle className="w-4 h-4 text-amber-500" />}
              {isBlock && <XCircle className="w-4 h-4 text-red-500" />}
            </div>
            <div className="mt-4">
              <span className={`text-xs font-bold font-mono px-2 py-1 border-2 border-current shadow-[2px_2px_0_0_currentColor] ${isAllow ? "bg-green-400/10 text-green-600" : isFlag ? "bg-amber-400/10 text-amber-600" : "bg-red-500/10 text-red-600"}`}>
                {decVal}
              </span>
            </div>
          </div>

          {/* Stage 6: Execution */}
          <div className="bg-black text-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-4 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000]">
            <div className="flex items-center justify-between text-[10px] font-bold font-mono uppercase tracking-widest border-b-2 border-white/20 pb-2">
              <span>6. EXECUTION</span>
              <CheckSquare className="w-4 h-4" />
            </div>
            <div className="mt-4">
              <p className="text-xs font-bold font-mono uppercase tracking-widest truncate">
                {execution.status}
              </p>
              <p className="text-[9px] text-white/70 font-mono font-bold truncate mt-1">
                {execution.razorpay_payout_id || "NOT EXECUTED"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Pipeline Breakdown */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left Column: Request & Policy & Provenance */}
        <div className="space-y-6">
          {/* Request Details */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6">
            <h3 className="text-xs font-bold text-black font-mono uppercase tracking-widest mb-4 inline-block bg-black/5 px-2 py-1 border-2 border-black">
              1. Payout Instruction Payload
            </h3>
            <div className="space-y-3 text-xs font-mono font-bold uppercase tracking-widest">
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Transaction ID</span>
                <span className="text-black">{request.txn_id}</span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Agent ID</span>
                <span className="text-black underline decoration-black/30 underline-offset-4">{request.agent_id} ({request.agent_name})</span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Amount</span>
                <span className="text-black bg-black/5 px-1">₹{request.amount_inr} ({request.amount} paise)</span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Payee ID</span>
                <span className="text-black">{request.payee_id}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-black/60">Category</span>
                <span className="text-black">{request.category}</span>
              </div>
            </div>
          </div>

          {/* Policy Evaluation */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6">
            <h3 className="text-xs font-bold text-black font-mono uppercase tracking-widest mb-4 flex items-center justify-between">
              <span className="inline-block bg-black/5 px-2 py-1 border-2 border-black">2. Deterministic Policy Mandate</span>
              <span
                className={`px-3 py-1 border-2 shadow-[2px_2px_0_0_#000] text-[10px] font-mono ${
                  policy.policy_allowed ? "border-green-500 text-green-600 bg-[#FDFBF7]" : "border-red-500 text-red-600 bg-[#FDFBF7]"
                }`}
              >
                {policy.policy_allowed ? "PASSED" : "VIOLATED"}
              </span>
            </h3>
            <div className="space-y-3 text-xs font-mono font-bold uppercase tracking-widest">
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Mandate ID</span>
                <span className="text-black">{policy.mandate_id || "N/A"}</span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Txn Cap</span>
                <span className="text-black">
                  {policy.txn_cap ? `₹${(policy.txn_cap / 100).toFixed(2)}` : "Unlimited"}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Daily Cap</span>
                <span className="text-black">
                  {policy.daily_cap ? `₹${(policy.daily_cap / 100).toFixed(2)}` : "Unlimited"}
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-black/60">Policy Reason</span>
                <span className={`px-2 py-1 border-2 font-bold shadow-[2px_2px_0_0_#000] inline-block ${policy.policy_allowed ? "border-green-500 text-green-600 bg-[#FDFBF7]" : "border-red-500 text-red-600 bg-[#FDFBF7]"}`}>
                  {policy.policy_reason || "AUTHORIZED"}
                </span>
              </div>
            </div>
          </div>

          {/* Provenance Evaluation */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6">
            <h3 className="text-xs font-bold text-black font-mono uppercase tracking-widest mb-4 inline-block bg-black/5 px-2 py-1 border-2 border-black">
              4. Intent Provenance Trace
            </h3>
            <div className="space-y-3 text-xs font-mono font-bold uppercase tracking-widest">
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Source Trust</span>
                <ProvenanceBadge trust={provenance.source_trust} size="sm" />
              </div>
              <div className="flex justify-between py-2 border-b-2 border-black/10">
                <span className="text-black/60">Origin Type</span>
                <span className="text-black">{provenance.source_type}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-black/60">Origin ID</span>
                <span className="text-black">{provenance.source_id}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Behavioral & Decision & Execution & Audit */}
        <div className="space-y-6">
          {/* Behavioral Anomaly Evaluation */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6">
            <h3 className="text-xs font-bold text-black font-mono uppercase tracking-widest mb-4 flex items-center justify-between">
              <span className="inline-block bg-black/5 px-2 py-1 border-2 border-black">3. Behavioral Anomaly Model</span>
              <span className="text-[10px] text-black font-mono border-2 border-black px-2 py-1 shadow-[2px_2px_0_0_#000]">{behavior.model_version}</span>
            </h3>
            <div className="mb-6 bg-black text-[#FDFBF7] border-2 border-black p-4 shadow-[4px_4px_0_0_#000] flex items-center justify-between">
              <div>
                <p className="text-[10px] text-white/70 font-mono font-bold uppercase tracking-widest mb-1">Isolation Forest Score</p>
                <p
                  className={`text-2xl font-bold font-mono ${
                    (behavior.anomaly_score ?? 0) >= 0.42 ? "text-amber-400" : "text-green-400"
                  }`}
                >
                  {behavior.anomaly_score !== null ? behavior.anomaly_score?.toFixed(3) : "N/A"}
                </p>
              </div>
              <div className="text-right border-l-2 border-white/20 pl-4">
                <p className="text-[10px] text-white/70 font-mono font-bold uppercase tracking-widest mb-1">Flag Threshold</p>
                <p className="text-base font-mono text-white font-bold">0.420</p>
              </div>
            </div>

            {/* Feature Signals summary */}
            <div className="space-y-3">
              <p className="text-[10px] font-mono text-black font-bold uppercase tracking-widest bg-black/5 px-2 py-1 inline-block border-2 border-black">
                Evaluated Behavioral Features
              </p>
              <div className="grid grid-cols-2 gap-3 text-[11px] font-mono font-bold uppercase tracking-widest">
                {Object.entries(behavior.canonical_features || {}).map(([key, val]) => (
                  <div key={key} className="bg-[#FDFBF7] px-3 py-2 border-2 border-black shadow-[2px_2px_0_0_#000] flex justify-between">
                    <span className="text-black/60 truncate pr-2">{key}</span>
                    <span className="text-black">{val.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Governor Final Decision */}
          <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6">
            <h3 className="text-xs font-bold text-black font-mono uppercase tracking-widest mb-4 inline-block bg-black/5 px-2 py-1 border-2 border-black">
              5 & 6. Governor Decision & Execution Gate
            </h3>
            <div className="p-5 bg-black text-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] space-y-5">
              <div className="flex items-center justify-between pb-4 border-b-2 border-white/20">
                <span className="text-xs font-mono font-bold uppercase tracking-widest text-white/70">Final Risk Decision:</span>
                <span
                  className={`px-4 py-2 text-sm font-bold font-mono border-2 border-current shadow-[2px_2px_0_0_currentColor] ${
                    isAllow
                      ? "border-green-400 text-green-400 bg-black"
                      : isFlag
                      ? "border-amber-400 text-amber-400 bg-black"
                      : "border-red-500 text-red-500 bg-black"
                  }`}
                >
                  {decVal}
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs font-mono font-bold uppercase tracking-widest pb-4 border-b-2 border-white/20 gap-3">
                <span className="text-white/70">RazorpayX Payout Gate:</span>
                <div className="font-bold text-right">
                  {execution.razorpay_payout_id ? (
                    <div className="flex flex-col items-end space-y-1">
                      <span className="text-green-400 bg-white/10 px-2 py-1 border-2 border-green-400 inline-block">EXECUTED</span>
                      <span className="text-[10px] text-green-400/80">{execution.razorpay_payout_id}</span>
                    </div>
                  ) : (
                    <span className="text-red-400 bg-white/10 px-2 py-1 border-2 border-red-400 inline-block text-center">NEVER EXECUTED<br/><span className="text-[10px]">(GATE CLOSED)</span></span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[10px] font-mono text-white/70 uppercase tracking-widest font-bold block mb-3">
                  Aggregated Reason Codes
                </span>
                <div className="flex flex-wrap gap-2">
                  {decision.reason_codes.map((rc, idx) => (
                    <span key={idx} className="px-3 py-1 bg-white text-black border-2 border-black text-[10px] font-mono font-bold tracking-widest uppercase shadow-[2px_2px_0_0_#000]">
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
