"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AgentSummary, AgentDetail } from "@/lib/types";
import { Users, Shield, Activity, X, ChevronRight } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [agentDetail, setAgentDetail] = useState<AgentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchAgents = async () => {
    try {
      setError(null);
      const data = await api.getAgents();
      setAgents(data);
    } catch (err: any) {
      setError(err.message || "Failed to load agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const openDetail = async (agentId: string) => {
    setSelectedAgentId(agentId);
    setDetailLoading(true);
    try {
      const detail = await api.getAgentDetail(agentId);
      setAgentDetail(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-tight">
            Governed AI Agents
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Real agents, authority mandates, daily utilization & transaction activity
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-[#11161D] px-3 py-1.5 rounded-lg border border-[#232B36]">
          Total Governed Agents: <strong className="text-white">{agents.length}</strong>
        </span>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#11161D] h-16 rounded-xl border border-[#232B36]" />
          ))}
        </div>
      ) : (
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-[#171D25] text-slate-400 border-b border-[#232B36] uppercase text-[10px] tracking-wider">
                <th className="p-3">Agent</th>
                <th className="p-3">Status</th>
                <th className="p-3">Mandate ID</th>
                <th className="p-3">Daily Cap / Used</th>
                <th className="p-3">Weekly Cap / Used</th>
                <th className="p-3">Utilization</th>
                <th className="p-3">Transactions</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232B36]">
              {agents.map((a) => (
                <tr
                  key={a.agent_id}
                  onClick={() => openDetail(a.agent_id)}
                  className="hover:bg-[#171D25]/60 transition-colors cursor-pointer"
                >
                  <td className="p-3 font-bold text-white">
                    <div>
                      <span className="text-slate-200">{a.name}</span>
                      <span className="block text-[10px] text-slate-500">{a.agent_id}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        a.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border border-red-500/20"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300">
                    {a.mandate_id ? (
                      <span className="text-[#3395FF]">{a.mandate_id}</span>
                    ) : (
                      <span className="text-slate-500">NO MANDATE</span>
                    )}
                  </td>
                  <td className="p-3 text-slate-300">
                    ₹{a.daily_usage_inr} / ₹{a.daily_cap_inr}
                  </td>
                  <td className="p-3 text-slate-300">
                    ₹{a.weekly_usage_inr} / ₹{a.weekly_cap_inr}
                  </td>
                  <td className="p-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-[#0B0F14] h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            a.utilization_pct > 80
                              ? "bg-red-500"
                              : a.utilization_pct > 50
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                          }`}
                          style={{ width: `${Math.min(100, a.utilization_pct)}%` }}
                        />
                      </div>
                      <span className="text-slate-300 font-bold">{a.utilization_pct}%</span>
                    </div>
                  </td>
                  <td className="p-3 text-slate-300 font-bold">{a.transaction_count}</td>
                  <td className="p-3 text-right">
                    <button className="text-slate-400 hover:text-[#3395FF] p-1">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Agent Detail Modal / Drawer */}
      {selectedAgentId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-xl bg-[#11161D] border-l border-[#232B36] h-full p-6 overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-[#232B36] pb-4">
              <div>
                <h3 className="text-lg font-bold text-white font-mono">Agent Detail Overview</h3>
                <p className="text-xs text-slate-400 font-mono">{selectedAgentId}</p>
              </div>
              <button
                onClick={() => setSelectedAgentId(null)}
                className="p-1 rounded hover:bg-[#171D25] text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading || !agentDetail ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                Loading agent profile & recent transactions...
              </div>
            ) : (
              <div className="space-y-6 text-xs font-mono">
                {/* Agent Summary Header */}
                <div className="bg-[#171D25] p-4 rounded-xl border border-[#232B36] space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Agent Name</span>
                    <span className="font-bold text-white">{agentDetail.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Mandate Status</span>
                    <span className="text-emerald-400 font-bold">{agentDetail.mandate_status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Daily Cap Utilization</span>
                    <span className="text-white font-bold">{agentDetail.utilization_pct}%</span>
                  </div>
                </div>

                {/* Mandate Constraints */}
                {agentDetail.mandate && (
                  <div className="bg-[#171D25] p-4 rounded-xl border border-[#232B36] space-y-2">
                    <h4 className="text-slate-300 font-bold uppercase text-[10px] tracking-wider mb-2">
                      Active Mandate Configuration
                    </h4>
                    <div className="flex justify-between py-1 border-b border-[#232B36]">
                      <span className="text-slate-400">Mandate ID</span>
                      <span className="text-[#3395FF]">{agentDetail.mandate.mandate_id}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#232B36]">
                      <span className="text-slate-400">Single Txn Cap</span>
                      <span className="text-emerald-400 font-bold">₹{agentDetail.mandate.txn_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#232B36]">
                      <span className="text-slate-400">Daily Limit</span>
                      <span className="text-slate-200">₹{agentDetail.mandate.daily_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#232B36]">
                      <span className="text-slate-400">Weekly Limit</span>
                      <span className="text-slate-200">₹{agentDetail.mandate.weekly_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Allowed Categories</span>
                      <span className="text-slate-300">
                        {agentDetail.mandate.allowed_categories.join(", ")}
                      </span>
                    </div>
                  </div>
                )}

                {/* Recent Transactions */}
                <div>
                  <h4 className="text-slate-300 font-bold uppercase text-[10px] tracking-wider mb-3">
                    Recent Transactions ({agentDetail.recent_transactions.length})
                  </h4>
                  {agentDetail.recent_transactions.length === 0 ? (
                    <p className="text-slate-500">No transaction activity recorded for this agent.</p>
                  ) : (
                    <div className="space-y-2">
                      {agentDetail.recent_transactions.map((t) => (
                        <div
                          key={t.txn_id}
                          className="bg-[#171D25] p-3 rounded-lg border border-[#232B36] flex items-center justify-between"
                        >
                          <div>
                            <span className="text-white font-bold block">{t.txn_id}</span>
                            <span className="text-[10px] text-slate-400">{t.payee_id} • {t.category}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-emerald-400 font-bold block">₹{t.amount_inr}</span>
                            <span
                              className={`text-[10px] font-bold ${
                                t.decision === "ALLOW"
                                  ? "text-emerald-400"
                                  : t.decision === "FLAG"
                                  ? "text-amber-400"
                                  : "text-red-400"
                              }`}
                            >
                              {t.decision}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
