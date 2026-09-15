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

  const handleDeactivate = async () => {
    if (!selectedAgentId) return;
    const token = window.prompt("Operator Action: Enter Admin Token to deactivate this agent:");
    if (!token) return;
    try {
      await api.deactivateAgent(selectedAgentId, token);
      alert("Agent successfully deactivated.");
      setSelectedAgentId(null);
      fetchAgents();
    } catch (err: any) {
      alert("Failed to deactivate: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h2 className="text-xl font-bold text-black font-mono tracking-tight uppercase">
            Governed Agent Profiles
          </h2>
          <p className="text-xs text-black/60 font-mono mt-1 font-bold tracking-widest uppercase">
            Agent profiles, authority mandates & daily utilization
          </p>
        </div>
        <span className="text-xs font-mono font-bold tracking-widest text-black bg-[#FDFBF7] px-4 py-2 border-2 border-black shadow-[4px_4px_0_0_#000] uppercase">
          Total Agents: <strong className="text-black ml-2">{agents.length}</strong>
        </span>
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#FDFBF7] h-16 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          ))}
        </div>
      ) : (
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono font-bold uppercase tracking-widest">
            <thead>
              <tr className="bg-black text-[#FDFBF7] border-b-2 border-black text-[10px]">
                <th className="p-4">Agent</th>
                <th className="p-4">Status</th>
                <th className="p-4">Mandate ID</th>
                <th className="p-4">Daily Cap / Used</th>
                <th className="p-4">Weekly Cap / Used</th>
                <th className="p-4">Utilization</th>
                <th className="p-4">Transactions</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-black text-black">
              {agents.map((a) => (
                <tr
                  key={a.agent_id}
                  onClick={() => openDetail(a.agent_id)}
                  className="hover:bg-black/5 transition-colors cursor-pointer"
                >
                  <td className="p-4">
                    <div>
                      <span className="text-black">{a.name}</span>
                      <span className="block text-[10px] text-black/60 mt-1">{a.agent_id}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-1 text-[10px] border-2 shadow-[2px_2px_0_0_#000] inline-block ${
                        a.status === "ACTIVE"
                          ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                          : "border-red-500 text-red-600 bg-[#FDFBF7]"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="p-4">
                    {a.mandate_id ? (
                      <span className="text-black bg-black/5 px-2 py-1 border-2 border-black">{a.mandate_id}</span>
                    ) : (
                      <span className="text-black/40">NO MANDATE</span>
                    )}
                  </td>
                  <td className="p-4">
                    ₹{a.daily_usage_inr} / ₹{a.daily_cap_inr}
                  </td>
                  <td className="p-4">
                    ₹{a.weekly_usage_inr} / ₹{a.weekly_cap_inr}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-16 bg-[#FDFBF7] border-2 border-black h-3 overflow-hidden shadow-[2px_2px_0_0_#000]">
                        <div
                          className={`h-full border-r-2 border-black ${
                            a.utilization_pct > 80
                              ? "bg-red-500"
                              : a.utilization_pct > 50
                              ? "bg-amber-400"
                              : "bg-green-400"
                          }`}
                          style={{ width: `${Math.min(100, a.utilization_pct)}%` }}
                        />
                      </div>
                      <span className="text-black">{a.utilization_pct}%</span>
                    </div>
                  </td>
                  <td className="p-4 text-black">{a.transaction_count}</td>
                  <td className="p-4 text-right">
                    <button className="text-black hover:text-[#FDFBF7] hover:bg-black p-1 border-2 border-transparent hover:border-black transition-colors">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Agent Detail Drawer */}
      {selectedAgentId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-xl bg-[#FDFBF7] border-l-4 border-black h-full p-8 overflow-y-auto space-y-8 font-mono shadow-[-12px_0_0_0_rgba(0,0,0,1)]">
            <div className="flex items-center justify-between border-b-4 border-black pb-6">
              <div>
                <h3 className="text-xl font-bold text-black uppercase">Agent Profile</h3>
                <p className="text-xs text-black/60 font-bold tracking-widest mt-1">{selectedAgentId}</p>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleDeactivate}
                  className="px-4 py-2 bg-red-100 border-2 border-red-500 text-red-600 shadow-[4px_4px_0_0_#ef4444] hover:bg-red-500 hover:text-white transition-all text-xs tracking-widest font-bold uppercase"
                >
                  Deactivate Agent
                </button>
                <button
                  onClick={() => setSelectedAgentId(null)}
                  className="p-2 bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] text-black hover:bg-black hover:text-[#FDFBF7] hover:translate-y-1 hover:shadow-none transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {detailLoading || !agentDetail ? (
              <div className="p-8 text-center text-black font-bold uppercase text-xs border-2 border-dashed border-black">
                Loading profile data...
              </div>
            ) : (
              <div className="space-y-8 text-xs font-bold uppercase tracking-widest">
                {/* Agent Summary Header */}
                <div className="bg-[#FDFBF7] p-6 border-2 border-black shadow-[6px_6px_0_0_#000] space-y-4 text-black">
                  <div className="flex justify-between border-b-2 border-black pb-2">
                    <span className="text-black/60">Agent Name</span>
                    <span className="text-black text-sm">{agentDetail.name}</span>
                  </div>
                  <div className="flex justify-between border-b-2 border-black pb-2">
                    <span className="text-black/60">Mandate Status</span>
                    <span className="text-green-600 bg-[#FDFBF7] px-2 py-0.5 border-2 border-green-500 shadow-[2px_2px_0_0_#22c55e]">{agentDetail.mandate_status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-black/60">Daily Cap Utilization</span>
                    <span className="text-black">{agentDetail.utilization_pct}%</span>
                  </div>
                </div>

                {/* Mandate Constraints */}
                {agentDetail.mandate && (
                  <div className="bg-[#FDFBF7] p-6 border-2 border-black shadow-[6px_6px_0_0_#000] space-y-4 text-black">
                    <h4 className="text-black bg-black text-[#FDFBF7] inline-block px-3 py-1 mb-2 text-[10px]">
                      Active Mandate Configuration
                    </h4>
                    <div className="flex justify-between py-2 border-b-2 border-black border-dashed">
                      <span className="text-black/60">Mandate ID</span>
                      <span className="text-black bg-black/5 px-2 py-0.5 border-2 border-black">{agentDetail.mandate.mandate_id}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b-2 border-black border-dashed">
                      <span className="text-black/60">Single Txn Cap</span>
                      <span className="text-black">₹{agentDetail.mandate.txn_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b-2 border-black border-dashed">
                      <span className="text-black/60">Daily Limit</span>
                      <span className="text-black">₹{agentDetail.mandate.daily_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b-2 border-black border-dashed">
                      <span className="text-black/60">Weekly Limit</span>
                      <span className="text-black">₹{agentDetail.mandate.weekly_cap / 100}</span>
                    </div>
                    <div className="flex justify-between py-2">
                      <span className="text-black/60">Allowed Categories</span>
                      <span className="text-black text-right max-w-[200px]">
                        {agentDetail.mandate.allowed_categories.join(", ")}
                      </span>
                    </div>
                  </div>
                )}

                {/* Recent Transactions */}
                <div>
                  <h4 className="text-black mb-4">
                    Recent Transactions <span className="bg-black text-[#FDFBF7] px-2 py-0.5 ml-2">{agentDetail.recent_transactions.length}</span>
                  </h4>
                  {agentDetail.recent_transactions.length === 0 ? (
                    <p className="text-black/60 border-2 border-dashed border-black p-4 text-center">No transaction activity recorded.</p>
                  ) : (
                    <div className="space-y-4">
                      {agentDetail.recent_transactions.map((t) => (
                        <div
                          key={t.txn_id}
                          className="bg-[#FDFBF7] p-4 border-2 border-black shadow-[4px_4px_0_0_#000] flex items-center justify-between hover:translate-x-1 hover:-translate-y-1 transition-transform"
                        >
                          <div>
                            <span className="text-black block text-sm mb-1">{t.txn_id}</span>
                            <span className="text-[10px] text-black/60">{t.payee_id} • {t.category}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-black block text-sm mb-1">₹{t.amount_inr}</span>
                            <span
                              className={`text-[10px] border-2 px-2 py-0.5 inline-block ${
                                t.decision === "ALLOW" || t.decision === "SUCCEEDED"
                                  ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                                  : t.decision === "FLAG"
                                  ? "border-amber-500 text-amber-600 bg-[#FDFBF7]"
                                  : "border-red-500 text-red-600 bg-[#FDFBF7]"
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
