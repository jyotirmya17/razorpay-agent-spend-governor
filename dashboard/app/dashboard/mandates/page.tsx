"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { MandateSummary } from "@/lib/types";
import { AlertOctagon, CheckCircle2, RefreshCw } from "lucide-react";

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
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h2 className="text-xl font-bold text-black font-mono tracking-tight uppercase">
            Policy Mandates Engine
          </h2>
          <p className="text-xs text-black/60 font-mono mt-1 font-bold tracking-widest uppercase">
            Deterministic spending limits & payee white-lists
          </p>
        </div>
        <span className="text-xs font-mono font-bold tracking-widest text-black bg-[#FDFBF7] px-4 py-2 border-2 border-black shadow-[4px_4px_0_0_#000] uppercase">
          Total Mandates: <strong className="text-black ml-2">{mandates.length}</strong>
        </span>
      </div>

      {revokeSuccess && (
        <div className="p-4 bg-[#FDFBF7] text-green-600 border-2 border-green-500 shadow-[4px_4px_0_0_#22c55e] text-xs font-mono font-bold uppercase tracking-widest flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{revokeSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest flex items-center space-x-2">
          ✕ Error: {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-[#FDFBF7] h-20 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          ))}
        </div>
      ) : (
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono font-bold uppercase tracking-widest">
            <thead>
              <tr className="bg-black text-[#FDFBF7] border-b-2 border-black text-[10px]">
                <th className="p-4">Mandate ID</th>
                <th className="p-4">Agent</th>
                <th className="p-4">Status</th>
                <th className="p-4">Txn Cap</th>
                <th className="p-4">Daily Cap / Usage</th>
                <th className="p-4">Weekly Cap</th>
                <th className="p-4">Allowed Categories</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-black text-black">
              {mandates.map((m) => (
                <tr key={m.mandate_id} className="hover:bg-black/5 transition-colors">
                  <td className="p-4 font-bold text-black underline underline-offset-4 decoration-black/30">
                    {m.mandate_id}
                    <span className="block text-[10px] text-black/60 font-normal mt-1 no-underline">v{m.version}</span>
                  </td>
                  <td className="p-4 font-bold text-black">{m.agent_id}</td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-1 text-[10px] font-bold border-2 shadow-[2px_2px_0_0_#000] inline-block ${
                        m.status === "ACTIVE"
                          ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                          : "border-red-500 text-red-600 bg-[#FDFBF7]"
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="p-4 text-black">₹{m.txn_cap_inr}</td>
                  <td className="p-4 text-black">
                    ₹{m.daily_usage_inr} / ₹{m.daily_cap_inr}
                  </td>
                  <td className="p-4 text-black">₹{m.weekly_cap_inr}</td>
                  <td className="p-4 text-black/70">
                    {m.allowed_categories.join(", ")}
                  </td>
                  <td className="p-4 text-right">
                    {m.status === "ACTIVE" ? (
                      <button
                        onClick={() => setRevokingMandate(m)}
                        className="px-3 py-1.5 bg-[#FDFBF7] hover:bg-red-500 hover:text-[#FDFBF7] text-red-600 border-2 border-red-500 font-bold transition-all text-[10px] shadow-[2px_2px_0_0_#ef4444] hover:shadow-none hover:translate-y-0.5"
                      >
                        REVOKE MANDATE
                      </button>
                    ) : (
                      <span className="text-black/50 text-[10px] bg-black/5 px-2 py-1 border-2 border-black/20">REVOKED</span>
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
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#FDFBF7] border-4 border-black shadow-[16px_16px_0_0_#000] p-8 max-w-md w-full space-y-6 font-mono font-bold uppercase tracking-widest text-black">
            <div className="flex items-center space-x-3 text-red-500 border-b-2 border-black pb-4">
              <AlertOctagon className="w-8 h-8 shrink-0" />
              <h3 className="text-xl">Revoke Policy?</h3>
            </div>

            <p className="text-xs text-black/70 leading-relaxed">
              Are you sure you want to revoke mandate <strong className="text-red-500">{revokingMandate.mandate_id}</strong> for agent <strong className="text-black">{revokingMandate.agent_id}</strong>?
            </p>

            <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-[11px] space-y-2">
              <p className="underline underline-offset-4 decoration-red-500/30">Immediate Governance Effect:</p>
              <p className="opacity-90">
                All subsequent payout requests from agent <strong>{revokingMandate.agent_id}</strong> will pass through the Governor policy engine and be strictly <strong>DENIED</strong>.
              </p>
            </div>

            <div className="flex justify-end space-x-4 pt-4 border-t-2 border-black">
              <button
                onClick={() => setRevokingMandate(null)}
                disabled={revoking}
                className="px-4 py-2 bg-[#FDFBF7] hover:bg-black text-black hover:text-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 transition-all text-xs disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRevokeConfirm}
                disabled={revoking}
                className="px-4 py-2 bg-[#FDFBF7] hover:bg-red-50 text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] hover:shadow-none hover:translate-y-1 transition-all text-xs flex items-center space-x-2 disabled:opacity-50"
              >
                {revoking ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Revoking...</span>
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
