"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Shield,
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Activity,
  ArrowRight,
  Info,
  CheckSquare
} from "lucide-react";
import { api } from "@/lib/api";
import { OverviewStats, TransactionSummary, SystemHealth } from "@/lib/types";

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [recentTxns, setRecentTxns] = useState<TransactionSummary[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [evalMetrics, setEvalMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const [s, t, h, m] = await Promise.all([
        api.getOverviewStats(),
        api.getTransactions({ page: 1, page_size: 6 }),
        api.getHealth(),
        api.getEvaluationMetrics(),
      ]);
      setStats(s);
      setRecentTxns(t.items || []);
      setHealth(h);
      setEvalMetrics(m);
    } catch (err: any) {
      setError(err.message || "Failed to load governor overview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    window.addEventListener("governor_refresh", loadData);
    const interval = setInterval(loadData, 10000);
    return () => {
      window.removeEventListener("governor_refresh", loadData);
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse bg-[#FDFBF7] h-32 border-2 border-black shadow-[4px_4px_0_0_#000]" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#FDFBF7] h-24 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Intro for Judges - Explaining the Product clearly */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 lg:p-8 flex flex-col lg:flex-row gap-8 justify-between relative overflow-hidden">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-4">
            <div className="inline-flex items-center space-x-2 bg-black text-[#FDFBF7] px-3 py-1 text-xs font-mono font-bold uppercase tracking-widest border-2 border-black shadow-[2px_2px_0_0_#000]">
              <Shield className="w-3.5 h-3.5" />
              <span>Razorpay AI Buildathon 2026</span>
            </div>
            <div className="inline-flex items-center space-x-2 bg-yellow-400 text-black px-3 py-1 text-xs font-mono font-bold uppercase tracking-widest border-2 border-black shadow-[2px_2px_0_0_#000] animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>DEMO ENVIRO</span>
            </div>
          </div>
          <h2 className="text-3xl lg:text-4xl font-bold text-black tracking-tight font-mono uppercase mt-4">
            Agent Spend Governor
          </h2>
          <p className="text-black/80 text-sm lg:text-base leading-relaxed font-bold font-mono tracking-wide">
            Autonomous AI Agents are being given access to corporate wallets. We protect these financial rails by adding a governance layer that evaluates <strong className="text-black bg-yellow-200 px-1">Behavior</strong>, <strong className="text-black bg-blue-200 px-1">Policies</strong>, and <strong className="text-black bg-green-200 px-1">Provenance</strong> before any RazorpayX payout is executed.
          </p>
        </div>

        <div className="flex flex-col justify-end space-y-4 lg:min-w-[280px]">
          <div className="bg-black/5 p-4 border-2 border-black font-mono text-xs font-bold uppercase tracking-widest">
            <div className="flex items-center justify-between mb-2">
              <span className="text-black/60">Live Protection</span>
              <span className="flex items-center space-x-1 text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Active</span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-black/60">Mode</span>
              <span className="text-black">Test Mode</span>
            </div>
          </div>
          <Link
            href="/dashboard/demo"
            className="w-full text-center px-4 py-3 border-2 border-black bg-black text-[#FDFBF7] hover:bg-[#FDFBF7] hover:text-black transition-colors shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 font-mono font-bold uppercase tracking-widest flex items-center justify-center space-x-2 group"
          >
            <span>Run Governance Scenarios</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-600 shadow-[4px_4px_0_0_#dc2626] font-mono font-bold uppercase text-xs flex items-center space-x-3">
          <XCircle className="w-5 h-5" />
          <span>Backend API Error: {error}</span>
        </div>
      )}

      {/* Decision Breakdown Cards - Redesigned with borders instead of solid fills */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6 relative flex flex-col justify-between hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#000] transition-all">
          <div className="absolute top-0 left-0 w-full h-2 bg-green-400 border-b-2 border-black" />
          <div className="flex justify-between items-start pt-2">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-black/60 block mb-1">ALLOW Decisions</span>
              <p className="text-4xl font-bold font-mono tabular-nums text-black">
                {stats?.decisions?.ALLOW || 0}
              </p>
            </div>
            <div className="bg-green-400 border-2 border-black p-2 shadow-[2px_2px_0_0_#000]">
              <CheckCircle2 className="w-6 h-6 text-black" />
            </div>
          </div>
          <p className="text-[10px] text-black/70 font-mono mt-4 uppercase tracking-wider font-bold">
            Authorized normal spend passing all behavioral and policy checks.
          </p>
        </div>

        <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6 relative flex flex-col justify-between hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#000] transition-all">
          <div className="absolute top-0 left-0 w-full h-2 bg-amber-400 border-b-2 border-black" />
          <div className="flex justify-between items-start pt-2">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-black/60 block mb-1">REVIEW Decisions</span>
              <p className="text-4xl font-bold font-mono tabular-nums text-black">
                {stats?.decisions?.REVIEW || 0}
              </p>
            </div>
            <div className="bg-amber-400 border-2 border-black p-2 shadow-[2px_2px_0_0_#000]">
              <AlertTriangle className="w-6 h-6 text-black" />
            </div>
          </div>
          <p className="text-[10px] text-black/70 font-mono mt-4 uppercase tracking-wider font-bold">
            Anomalous behavior or untrusted source detected. Execution paused.
          </p>
        </div>

        <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-6 relative flex flex-col justify-between hover:-translate-y-1 hover:shadow-[8px_8px_0_0_#000] transition-all">
          <div className="absolute top-0 left-0 w-full h-2 bg-red-500 border-b-2 border-black" />
          <div className="flex justify-between items-start pt-2">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-black/60 block mb-1">DENY Decisions</span>
              <p className="text-4xl font-bold font-mono tabular-nums text-black">
                {stats?.decisions?.DENY || 0}
              </p>
            </div>
            <div className="bg-red-500 border-2 border-black p-2 shadow-[2px_2px_0_0_#000]">
              <XCircle className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-[10px] text-black/70 font-mono mt-4 uppercase tracking-wider font-bold">
            Hard policy violations (e.g., exceeding daily cap). Execution blocked.
          </p>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-5">
          <div className="flex items-center justify-between text-black text-xs font-mono font-bold uppercase tracking-widest mb-3">
            <span>Agents</span>
            <Users className="w-4 h-4 text-black/40" />
          </div>
          <p className="text-2xl font-bold text-black font-mono tabular-nums">
            {stats?.total_agents || 0}
          </p>
          <p className="text-[9px] text-black/50 mt-1 font-mono font-bold uppercase tracking-wider">Governed AI Profiles</p>
        </div>

        <div className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-5">
          <div className="flex items-center justify-between text-black text-xs font-mono font-bold uppercase tracking-widest mb-3">
            <span>Policies</span>
            <Shield className="w-4 h-4 text-black/40" />
          </div>
          <p className="text-2xl font-bold text-black font-mono tabular-nums">
            {stats?.active_mandates || 0}
          </p>
          <p className="text-[9px] text-black/50 mt-1 font-mono font-bold uppercase tracking-wider">Active Spend Limits</p>
        </div>

        <div className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-5">
          <div className="flex items-center justify-between text-black text-xs font-mono font-bold uppercase tracking-widest mb-3">
            <span>Volume</span>
            <CreditCard className="w-4 h-4 text-black/40" />
          </div>
          <p className="text-2xl font-bold text-black font-mono tabular-nums">
            ₹{(stats?.governed_amount_inr || 0).toLocaleString()}
          </p>
          <p className="text-[9px] text-black/50 mt-1 font-mono font-bold uppercase tracking-wider">Total Processed (INR)</p>
        </div>

        <div className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-5">
          <div className="flex items-center justify-between text-black text-xs font-mono font-bold uppercase tracking-widest mb-3">
            <span>Evaluations</span>
            <Activity className="w-4 h-4 text-black/40" />
          </div>
          <p className="text-2xl font-bold text-black font-mono tabular-nums">
            {stats?.total_transactions || 0}
          </p>
          <p className="text-[9px] text-black/50 mt-1 font-mono font-bold uppercase tracking-wider">Total Transactions</p>
        </div>
      </div>

      {/* Pipeline Diagram for Judges */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 lg:p-8 space-y-6">
        <div className="flex items-center justify-between border-b-2 border-black pb-4">
          <h3 className="text-sm lg:text-base font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2">
            <Info className="w-5 h-5" />
            <span>How The Pipeline Works</span>
          </h3>
          <span className="text-[10px] hidden md:inline-block font-mono font-bold bg-black/5 text-black px-3 py-1 uppercase tracking-widest border-2 border-black">
            Interceptors → AI Risk Model → Decision
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { step: "REQUEST", label: "Agent Payload", desc: "Agent makes a RazorpayX POST /v1/payout request." },
            { step: "POLICY", label: "Mandate Engine", desc: "Checks deterministic limits (e.g. daily caps)." },
            { step: "BEHAVIOR", label: "Anomaly Model", desc: "Isolation Forest checks if txn is unusual." },
            { step: "PROVENANCE", label: "Trust Evaluator", desc: "Checks if intent origin is trusted vs scraped." },
            { step: "DECISION", label: "Precedence Gate", desc: "Aggregates signals to ALLOW, FLAG, or BLOCK." },
            { step: "EXECUTION", label: "RazorpayX API", desc: "If ALLOWED, passes to actual payment gateway." },
          ].map((item, idx) => (
            <div
              key={item.step}
              className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-4 relative flex flex-col hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] transition-all"
            >
              <span className="text-[10px] font-mono font-bold uppercase tracking-widest bg-black text-[#FDFBF7] px-2 py-1 inline-block mb-3 self-start shadow-[2px_2px_0_0_#000]">
                0{idx + 1}. {item.step}
              </span>
              <p className="text-xs font-bold text-black uppercase mb-2">{item.label}</p>
              <p className="text-[10px] text-black/60 font-mono font-bold leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ML Evaluation Metrics */}
      {evalMetrics && Object.keys(evalMetrics).length > 0 && (
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 lg:p-8 space-y-6">
          <div className="flex items-center justify-between border-b-2 border-black pb-4">
            <h3 className="text-sm lg:text-base font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2">
              <Activity className="w-5 h-5" />
              <span>Offline Risk Model Evaluation (Phase 4.6)</span>
            </h3>
            <span className="text-[10px] hidden md:inline-block font-mono font-bold bg-amber-200 text-black px-3 py-1 uppercase tracking-widest border-2 border-black">
              Isolation Forest @ 0.42 Threshold
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="border-2 border-black p-4 bg-black/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono font-bold text-black/60 uppercase tracking-widest">Unseen Agent FPR</span>
              <span className="text-xl font-bold font-mono">{(evalMetrics.false_positive_rate * 100).toFixed(2)}%</span>
            </div>
            <div className="border-2 border-black p-4 bg-black/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono font-bold text-black/60 uppercase tracking-widest">F1 Score</span>
              <span className="text-xl font-bold font-mono">{evalMetrics.f1_score?.toFixed(3)}</span>
            </div>
            <div className="border-2 border-black p-4 bg-black/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono font-bold text-black/60 uppercase tracking-widest">Burst Recall</span>
              <span className="text-xl font-bold font-mono">{(evalMetrics.recall_burst * 100).toFixed(2)}%</span>
            </div>
            <div className="border-2 border-black p-4 bg-black/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono font-bold text-black/60 uppercase tracking-widest">Spike Recall</span>
              <span className="text-xl font-bold font-mono">{(evalMetrics.recall_spike * 100).toFixed(2)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Live Governance Feed */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 lg:p-8 space-y-6">
        <div className="flex items-center justify-between border-b-2 border-black pb-4">
          <h3 className="text-sm lg:text-base font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2">
            <CheckSquare className="w-5 h-5" />
            <span>Recent Pipeline Evaluations</span>
          </h3>
          <Link
            href="/dashboard/transactions"
            className="text-[10px] font-bold text-black hover:text-[#FDFBF7] hover:bg-black border-2 border-black px-4 py-2 shadow-[2px_2px_0_0_#000] hover:shadow-none uppercase font-mono tracking-widest transition-colors flex items-center space-x-2"
          >
            <span>View Audit Log</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {recentTxns.length === 0 ? (
          <div className="p-10 text-center text-black/50 font-mono font-bold uppercase text-xs border-2 border-dashed border-black/30 bg-black/5">
            No transactions processed yet. Navigate to Scenarios to seed activity.
          </div>
        ) : (
          <div className="space-y-4">
            {recentTxns.map((t) => (
              <div
                key={t.txn_id}
                className="bg-[#FDFBF7] border-2 border-black p-5 shadow-[4px_4px_0_0_#000] flex flex-col md:flex-row md:items-center justify-between text-xs font-mono font-bold uppercase tracking-wider hover:translate-x-1 hover:-translate-y-1 transition-transform gap-4"
              >
                <div className="flex items-start md:items-center space-x-4">
                  <span
                    className={`w-3 h-3 border-2 border-black shadow-[2px_2px_0_0_#000] flex-shrink-0 mt-1 md:mt-0 ${
                      t.decision === "ALLOW" || t.decision === "SUCCEEDED"
                        ? "bg-green-400"
                        : t.decision === "REVIEW"
                        ? "bg-amber-400"
                        : "bg-red-500"
                    }`}
                  />
                  <div>
                    <span className="text-black text-xs md:text-sm">{t.txn_id}</span>
                    <span className="text-black/60 text-[10px] block mt-1">
                      Agent: <strong className="text-black">{t.agent_id}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap md:flex-nowrap items-center gap-4 md:space-x-8 text-black">
                  <div className="md:text-right md:border-l-2 md:border-black/20 md:pl-6 w-full md:w-auto">
                    <span className="text-black/60 text-[10px] block mb-1">PAYEE / CAT</span>
                    <span>
                      {t.payee_id} <span className="text-black/50">({t.category})</span>
                    </span>
                  </div>

                  <div className="md:text-right md:border-l-2 md:border-black/20 md:pl-6 w-full md:w-auto">
                    <span className="text-black/60 text-[10px] block mb-1">AMOUNT</span>
                    <span className="text-black text-sm">₹{t.amount_inr}</span>
                  </div>

                  <div className="md:text-right md:border-l-2 md:border-black/20 md:pl-6 min-w-[120px] w-full md:w-auto">
                    <span className="text-black/60 text-[10px] block mb-1">DECISION</span>
                    <span
                      className={`inline-block border-2 border-black px-3 py-1 shadow-[2px_2px_0_0_#000] ${
                        t.decision === "ALLOW" || t.decision === "SUCCEEDED"
                          ? "bg-green-400 text-black"
                          : t.decision === "REVIEW"
                          ? "bg-amber-400 text-black"
                          : "bg-red-500 text-white"
                      }`}
                    >
                      {t.decision}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
