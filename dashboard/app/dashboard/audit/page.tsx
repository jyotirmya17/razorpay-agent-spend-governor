"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AuditEventItem } from "@/lib/types";
import { AuditVerifierButton } from "@/components/governance/AuditVerifierButton";
import { AuditChainViewer } from "@/components/governance/AuditChainViewer";
import { FileCheck } from "lucide-react";

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAuditEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAuditEvents(page, pageSize);
      setEvents(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load audit events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
  }, [page]);

  return (
    <div className="space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-tight">
            Tamper-Evident Audit Trail
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Cryptographic SHA-256 hash-chain sequence of all Governor decisions & state changes
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-[#11161D] px-3 py-1.5 rounded-lg border border-[#232B36]">
          Total Audit Events: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Audit Verifier Widget */}
      <AuditVerifierButton />

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Error: {error}
        </div>
      )}

      {/* Audit Event Stream */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#11161D] h-24 rounded-xl border border-[#232B36]" />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          <AuditChainViewer events={events} />

          {/* Pagination Controls */}
          <div className="bg-[#11161D] p-3 border border-[#232B36] rounded-xl flex items-center justify-between font-mono text-xs text-slate-400">
            <span>
              Page {page} of {Math.ceil(total / pageSize) || 1}
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-[#171D25] hover:bg-[#232B36] border border-[#232B36] rounded disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * pageSize >= total}
                className="px-3 py-1 bg-[#171D25] hover:bg-[#232B36] border border-[#232B36] rounded disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
