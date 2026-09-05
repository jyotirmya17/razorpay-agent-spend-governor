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
  ShieldCheck,
  RefreshCw,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { OverviewStats, TransactionSummary, SystemHealth } from "@/lib/types";
import { ProvenanceBadge } from "@/components/governance/ProvenanceBadge";

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [recentTxns, setRecentTxns] = useState<TransactionSummary[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const [s, t, h] = await Promise.all([
        api.getOverviewStats(),
        api.getTransactions({ page: 1, page_size: 6 }),
        api.getHealth(),
      ]);
      setStats(s);
      setRecentTxns(t.items || []);
      setHealth(h);
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
        <div className="animate-pulse bg-[#11161D] h-32 rounded-xl border border-[#232B36]" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#11161D] h-24 rounded-xl border border-[#232B36]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero & Core Thesis Card */}
      <div className="bg-gradient-to-r from-[#11161D] via-[#171D25] to-[#11161D] border border-[#232B36] rounded-xl p-6 relative overflow-hidden">
        <div className="max-w-3xl space-y-2">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20 text-xs font-mono font-bold">
            <Zap className="w-3.5 h-3.5" />
            <span>Autonomous AI Spend Protection Engine</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Agent Spend Governor
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            <strong className="text-white">Core Thesis:</strong> &ldquo;An authorized transaction can still be risky when agent behavior changes or the payment decision originates from untrusted content.&rdquo;
          </p>
        </div>

        <div className="mt-4 pt-4 border-t border-[#232B36]/60 flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-4">
            <span>Isolation Forest Anomaly Detection</span>
            <span>•</span>
            <span>SHA-256 Tamper-Evident Audit Chain</span>
            <span>•</span>
            <span>RazorpayX Test Mode Gate</span>
          </div>
          <Link
            href="/demo"
            className="px-3 py-1.5 bg-[#3395FF] hover:bg-[#2575d6] text-white font-bold rounded-lg transition-colors flex items-center space-x-1.5 text-xs"
          >
            <span>Open Demo Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-xs font-mono text-red-400">
          ✕ Backend API Error: {error}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-4 gap-4">
        {/* Total Agents */}
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>TOTAL AGENTS</span>
            <Users className="w-4 h-4 text-[#3395FF]" />
          </div>
          <div className="mt-3">
            <p className="text-2xl font-bold text-white font-mono tabular-nums">
              {stats?.total_agents || 0}
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">Active governed AI agents</p>
          </div>
        </div>

        {/* Active Mandates */}
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>ACTIVE MANDATES</span>
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <p className="text-2xl font-bold text-white font-mono tabular-nums">
              {stats?.active_mandates || 0}
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">Enforced spend policies</p>
          </div>
        </div>

        {/* Governed Amount */}
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>GOVERNED AMOUNT</span>
            <CreditCard className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <p className="text-2xl font-bold text-emerald-400 font-mono tabular-nums">
              ₹{(stats?.governed_amount_inr || 0).toLocaleString()}
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Total transaction volume processed
            </p>
          </div>
        </div>

        {/* Total Transactions */}
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>TOTAL EVALUATIONS</span>
            <Activity className="w-4 h-4 text-[#3395FF]" />
          </div>
          <div className="mt-3">
            <p className="text-2xl font-bold text-white font-mono tabular-nums">
              {stats?.total_transactions || 0}
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">Governor decisions logged</p>
          </div>
        </div>
      </div>

      {/* Decision Breakdown Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#11161D] border border-emerald-500/20 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-slate-400">ALLOW Decisions</span>
            <p className="text-xl font-bold text-emerald-400 font-mono mt-1 tabular-nums">
              {stats?.decisions?.ALLOW || 0}
            </p>
          </div>
          <CheckCircle2 className="w-8 h-8 text-emerald-400/80" />
        </div>

        <div className="bg-[#11161D] border border-amber-500/20 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-slate-400">FLAG Decisions</span>
            <p className="text-xl font-bold text-amber-400 font-mono mt-1 tabular-nums">
              {stats?.decisions?.FLAG || 0}
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-amber-400/80" />
        </div>

        <div className="bg-[#11161D] border border-red-500/20 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-slate-400">BLOCK Decisions</span>
            <p className="text-xl font-bold text-red-400 font-mono mt-1 tabular-nums">
              {stats?.decisions?.BLOCK || 0}
            </p>
          </div>
          <XCircle className="w-8 h-8 text-red-400/80" />
        </div>
      </div>

      {/* Pipeline Diagram */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Governor Orchestration Pipeline Architecture
          </h3>
          <span className="text-[10px] font-mono text-slate-400">
            Single entry point: POST /v1/payouts
          </span>
        </div>

        <div className="grid grid-cols-6 gap-2 pt-2">
          {[
            { step: "REQUEST", label: "Agent Payout Intent", desc: "Agent ID, Amount, Payee, Provenance" },
            { step: "POLICY", label: "Mandate Engine", desc: "Deterministic daily/weekly/txn caps" },
            { step: "BEHAVIOR", label: "Anomaly Model", desc: "Isolation Forest risk scoring" },
            { step: "PROVENANCE", label: "Trust Evaluator", desc: "Payment origin trust classification" },
            { step: "DECISION", label: "Precedence Gate", desc: "ALLOW / FLAG / BLOCK reason aggregation" },
            { step: "EXECUTION", label: "RazorpayX Execution", desc: "Strict execution gate (ALLOW only)" },
          ].map((item, idx) => (
            <div
              key={item.step}
              className="bg-[#171D25] border border-[#232B36] rounded-lg p-3 relative flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] font-mono text-[#3395FF] font-bold block">
                  0{idx + 1}. {item.step}
                </span>
                <p className="text-xs font-bold text-white mt-1">{item.label}</p>
              </div>
              <p className="text-[10px] text-slate-400 font-mono mt-2">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Live Governance Feed */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Live Governance Stream (Real Transactions)
          </h3>
          <Link
            href="/transactions"
            className="text-xs text-[#3395FF] hover:underline font-mono flex items-center space-x-1"
          >
            <span>View All Transactions</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {recentTxns.length === 0 ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs border border-dashed border-[#232B36] rounded-lg">
            No transactions processed yet. Run a scenario in the Demo Center to seed activity.
          </div>
        ) : (
          <div className="space-y-2">
            {recentTxns.map((t) => (
              <div
                key={t.txn_id}
                className="bg-[#171D25] border border-[#232B36] hover:border-[#3395FF]/30 transition-colors p-3 rounded-lg flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center space-x-4">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      t.decision === "ALLOW"
                        ? "bg-emerald-400"
                        : t.decision === "FLAG"
                        ? "bg-amber-400"
                        : "bg-red-400"
                    }`}
                  />
                  <div>
                    <span className="font-bold text-white">{t.txn_id}</span>
                    <span className="text-slate-500 text-[10px] ml-2">
                      Agent: <strong className="text-slate-300">{t.agent_id}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block">PAYEE / CAT</span>
                    <span className="text-slate-300">
                      {t.payee_id} ({t.category})
                    </span>
                  </div>

                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block">AMOUNT</span>
                    <span className="text-emerald-400 font-bold">₹{t.amount_inr}</span>
                  </div>

                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block">DECISION</span>
                    <span
                      className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                        t.decision === "ALLOW"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : t.decision === "FLAG"
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-red-500/10 text-red-400"
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
