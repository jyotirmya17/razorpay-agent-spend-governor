"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { AuditVerificationResult } from "@/lib/types";
import { ShieldCheck, RefreshCw, CheckCircle2, XCircle } from "lucide-react";

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
    <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] p-6 space-y-6">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h3 className="text-sm font-bold text-black font-mono uppercase tracking-widest flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-black" />
            <span>Cryptographic Audit Chain Verifier</span>
          </h3>
          <p className="text-xs text-black/60 font-mono font-bold tracking-widest mt-1 uppercase">
            Verifies SHA-256 hash-link sequence integrity
          </p>
        </div>

        <button
          onClick={handleVerify}
          disabled={loading}
          className="px-4 py-2 bg-black hover:bg-[#FDFBF7] text-[#FDFBF7] hover:text-black border-2 border-black font-mono font-bold text-xs uppercase tracking-widest shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 transition-all flex items-center space-x-2 disabled:opacity-50 disabled:hover:bg-black disabled:hover:text-[#FDFBF7] disabled:hover:shadow-[4px_4px_0_0_#000] disabled:hover:translate-y-0"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Verifying Hashes...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>VERIFY AUDIT INTEGRITY</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest">
          ✕ Verification Error: {error}
        </div>
      )}

      {result && (
        <div className="space-y-4 font-mono font-bold uppercase tracking-widest text-xs">
          {result.valid ? (
            <div className="p-4 bg-[#FDFBF7] text-green-600 border-2 border-green-500 shadow-[4px_4px_0_0_#22c55e] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5" />
                <span>✓ AUDIT CHAIN VALID — NO TAMPERING DETECTED</span>
              </div>
              <span className="text-[10px] bg-black text-[#FDFBF7] px-2 py-1 border-2 border-black">
                {result.events_checked} Events Verified
              </span>
            </div>
          ) : (
            <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <XCircle className="w-5 h-5" />
                <span>✕ AUDIT CHAIN INVALID / TAMPERED</span>
              </div>
              <span className="text-[10px] bg-black text-[#FDFBF7] px-2 py-1 border-2 border-black">
                Failed at Sequence #{result.failed_sequence_id}
              </span>
            </div>
          )}

          <div className="grid grid-cols-4 gap-4 text-[10px] text-black bg-black/5 p-4 border-2 border-black shadow-[4px_4px_0_0_#000]">
            <div className="border-r-2 border-black/10">
              <span className="block text-black/50 mb-1">TOTAL EVENTS</span>
              <span className="text-black text-xs">{result.events_checked}</span>
            </div>
            <div className="border-r-2 border-black/10 pl-4">
              <span className="block text-black/50 mb-1">FIRST SEQUENCE</span>
              <span className="text-black text-xs">#{result.first_sequence_id ?? 1}</span>
            </div>
            <div className="border-r-2 border-black/10 pl-4">
              <span className="block text-black/50 mb-1">LAST SEQUENCE</span>
              <span className="text-black text-xs">#{result.last_sequence_id ?? result.events_checked}</span>
            </div>
            <div className="pl-4">
              <span className="block text-black/50 mb-1">CHAIN STATUS</span>
              <span className={`text-xs ${result.valid ? "text-green-600" : "text-red-600"}`}>
                {result.valid ? "INTACT" : "CORRUPTED"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
