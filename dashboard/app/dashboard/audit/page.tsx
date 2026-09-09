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
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h2 className="text-xl font-bold text-black font-mono tracking-tight uppercase">
            Tamper-Evident Audit Trail
          </h2>
          <p className="text-xs text-black/60 font-mono mt-1 font-bold tracking-widest uppercase">
            Cryptographic SHA-256 hash-chain sequence
          </p>
        </div>
        <span className="text-xs font-mono font-bold tracking-widest text-black bg-[#FDFBF7] px-4 py-2 border-2 border-black shadow-[4px_4px_0_0_#000] uppercase">
          Total Events: <strong className="text-black ml-2 underline underline-offset-4 decoration-black/30">{total}</strong>
        </span>
      </div>

      {/* Audit Verifier Widget */}
      <div className="mb-6">
        <AuditVerifierButton />
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest flex items-center space-x-2">
          ✕ Error: {error}
        </div>
      )}

      {/* Audit Event Stream */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-[#FDFBF7] h-24 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <AuditChainViewer events={events} />

          {/* Pagination Controls */}
          <div className="bg-[#FDFBF7] p-4 border-2 border-black shadow-[8px_8px_0_0_#000] flex items-center justify-between font-mono font-bold uppercase tracking-widest text-xs text-black">
            <span>
              Page {page} of {Math.ceil(total / pageSize) || 1}
            </span>
            <div className="flex space-x-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-[#FDFBF7] hover:bg-black hover:text-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 transition-all disabled:opacity-40 disabled:hover:bg-[#FDFBF7] disabled:hover:text-black disabled:hover:translate-y-0 disabled:hover:shadow-[4px_4px_0_0_#000]"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * pageSize >= total}
                className="px-4 py-2 bg-[#FDFBF7] hover:bg-black hover:text-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-y-1 transition-all disabled:opacity-40 disabled:hover:bg-[#FDFBF7] disabled:hover:text-black disabled:hover:translate-y-0 disabled:hover:shadow-[4px_4px_0_0_#000]"
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
