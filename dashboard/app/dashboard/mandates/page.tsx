"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { MandateSummary } from "@/lib/types";
import { Shield, AlertOctagon, CheckCircle2, XCircle, RefreshCw } from "lucide-react";

export default function MandatesPage() {
  const [mandates, setMandates] = useState<MandateSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Revocation Modal state
  const [revokingMandate, setRevokingMandate] = useState<MandateSummary | null>(null);
  const [revoking, setRevoking] = useState(false);
  const [revokeSuccess, setRevokeSuccess] = useState<string | null>(null);

  const fetchMandates = async () => {
    try {
      setError(null);
      const data = await api.getMandates();
      setMandates(data);
    } catch (err: any) {
      setError(err.message || "Failed to load mandate policies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMandates();
  }, []);

  const handleRevokeConfirm = async () => {
    if (!revokingMandate) return;
    setRevoking(true);
    setRevokeSuccess(null);
    try {
      await api.revokeMandate(revokingMandate.mandate_id);
      setRevokeSuccess(`Mandate ${revokingMandate.mandate_id} was successfully REVOKED in PostgreSQL.`);
      setRevokingMandate(null);
      fetchMandates();
    } catch (err: any) {
      setError(err.message || "Revocation failed");
    } finally {
      setRevoking(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-tight">
            Policy Mandates Engine
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Deterministic spending limits, payee white-lists & active mandate controls
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-[#11161D] px-3 py-1.5 rounded-lg border border-[#232B36]">
          Total Mandates: <strong className="text-white">{mandates.length}</strong>
        </span>
      </div>

      {revokeSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs font-mono text-emerald-400 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{revokeSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-[#11161D] h-20 rounded-xl border border-[#232B36]" />
          ))}
        </div>
      ) : (
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-[#171D25] text-slate-400 border-b border-[#232B36] uppercase text-[10px] tracking-wider">
                <th className="p-3">Mandate ID</th>
                <th className="p-3">Agent</th>
                <th className="p-3">Status</th>
                <th className="p-3">Txn Cap</th>
                <th className="p-3">Daily Cap / Usage</th>
                <th className="p-3">Weekly Cap</th>
                <th className="p-3">Allowed Categories</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232B36]">
              {mandates.map((m) => (
                <tr key={m.mandate_id} className="hover:bg-[#171D25]/40 transition-colors">
                  <td className="p-3 font-bold text-[#3395FF]">
                    {m.mandate_id}
                    <span className="block text-[10px] text-slate-500 font-normal">v{m.version}</span>
                  </td>
                  <td className="p-3 font-bold text-white">{m.agent_id}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        m.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border border-red-500/20"
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="p-3 text-emerald-400 font-bold">₹{m.txn_cap_inr}</td>
                  <td className="p-3 text-slate-300">
                    ₹{m.daily_usage_inr} / ₹{m.daily_cap_inr}
                  </td>
                  <td className="p-3 text-slate-300">₹{m.weekly_cap_inr}</td>
                  <td className="p-3 text-slate-400">
                    {m.allowed_categories.join(", ")}
                  </td>
                  <td className="p-3 text-right">
                    {m.status === "ACTIVE" ? (
                      <button
                        onClick={() => setRevokingMandate(m)}
                        className="px-2.5 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded font-bold transition-colors text-[10px]"
                      >
                        REVOKE MANDATE
                      </button>
                    ) : (
                      <span className="text-slate-500 text-[10px]">REVOKED</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Revocation Confirmation Modal */}
      {revokingMandate && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#11161D] border border-red-500/30 rounded-xl p-6 max-w-md w-full space-y-4 font-mono">
            <div className="flex items-center space-x-3 text-red-400">
              <AlertOctagon className="w-6 h-6 shrink-0" />
              <h3 className="text-base font-bold text-white">Revoke Mandate Policy?</h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to revoke mandate <strong className="text-red-400">{revokingMandate.mandate_id}</strong> for agent <strong className="text-white">{revokingMandate.agent_id}</strong>?
            </p>

            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-[11px] text-red-300 space-y-1">
              <p className="font-bold">Immediate Governance Effect:</p>
              <p className="text-slate-300">
                All subsequent payout requests from agent <strong>{revokingMandate.agent_id}</strong> will pass through the Governor policy engine and be strictly <strong>BLOCKED</strong>.
              </p>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setRevokingMandate(null)}
                disabled={revoking}
                className="px-4 py-2 bg-[#171D25] hover:bg-[#232B36] text-slate-300 rounded-lg text-xs font-bold transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRevokeConfirm}
                disabled={revoking}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center space-x-1.5"
              >
                {revoking ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Revoking in PostgreSQL...</span>
                  </>
                ) : (
                  <span>CONFIRM REVOCATION</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
