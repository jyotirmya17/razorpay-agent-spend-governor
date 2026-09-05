"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { AuditVerificationResult } from "@/lib/types";
import { ShieldCheck, ShieldAlert, RefreshCw, CheckCircle2, XCircle } from "lucide-react";

export function AuditVerifierButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditVerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.verifyAuditChain();
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Audit chain verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#3395FF]" />
            <span>Cryptographic Audit Chain Verifier</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Verifies SHA-256 hash-link sequence integrity across all PostgreSQL audit events.
          </p>
        </div>

        <button
          onClick={handleVerify}
          disabled={loading}
          className="px-4 py-2 bg-[#3395FF] hover:bg-[#2575d6] text-white font-mono font-bold text-xs rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Verifying SHA-256 Hashes...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>VERIFY AUDIT INTEGRITY</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Verification Error: {error}
        </div>
      )}

      {result && (
        <div className="mt-4 pt-4 border-t border-[#232B36] space-y-3 font-mono text-xs">
          {result.valid ? (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-between text-emerald-400">
              <div className="flex items-center space-x-2 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>✓ AUDIT CHAIN VALID — NO TAMPERING DETECTED</span>
              </div>
              <span className="text-[10px] text-emerald-500">
                {result.events_checked} Events Verified
              </span>
            </div>
          ) : (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between text-red-400">
              <div className="flex items-center space-x-2 font-bold">
                <XCircle className="w-4 h-4" />
                <span>✕ AUDIT CHAIN INVALID / TAMPERED</span>
              </div>
              <span className="text-[10px] text-red-500">
                Failed at Sequence #{result.failed_sequence_id}
              </span>
            </div>
          )}

          <div className="grid grid-cols-4 gap-3 text-[11px] text-slate-400 bg-[#171D25] p-3 rounded-lg border border-[#232B36]">
            <div>
              <span className="block text-slate-500 text-[10px]">TOTAL EVENTS</span>
              <span className="text-white font-bold">{result.events_checked}</span>
            </div>
            <div>
              <span className="block text-slate-500 text-[10px]">FIRST SEQUENCE</span>
              <span className="text-white font-bold">#{result.first_sequence_id ?? 1}</span>
            </div>
            <div>
              <span className="block text-slate-500 text-[10px]">LAST SEQUENCE</span>
              <span className="text-white font-bold">#{result.last_sequence_id ?? result.events_checked}</span>
            </div>
            <div>
              <span className="block text-slate-500 text-[10px]">CHAIN STATUS</span>
              <span className={result.valid ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                {result.valid ? "INTACT" : "CORRUPTED"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
