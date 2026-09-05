"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { TransactionSummary, FullTransactionInvestigation } from "@/lib/types";
import { PipelineVisualizer } from "@/components/governance/PipelineVisualizer";
import { ProvenanceBadge } from "@/components/governance/ProvenanceBadge";
import {
  Search,
  Filter,
  CreditCard,
  ChevronRight,
  X,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from "lucide-react";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<TransactionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filter state
  const [decisionFilter, setDecisionFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Investigation drawer state
  const [selectedTxnId, setSelectedTxnId] = useState<string | null>(null);
  const [fullTxn, setFullTxn] = useState<FullTransactionInvestigation | null>(null);
  const [fullLoading, setFullLoading] = useState(false);

  const fetchTxns = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getTransactions({
        page,
        page_size: pageSize,
        decision: decisionFilter || undefined,
        search: searchQuery || undefined,
      });
      setTransactions(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load transactions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTxns();
  }, [page, decisionFilter, searchQuery]);

  const openInvestigation = async (txnId: string) => {
    setSelectedTxnId(txnId);
    setFullLoading(true);
    try {
      const detail = await api.getTransactionFull(txnId);
      setFullTxn(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setFullLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white font-mono tracking-tight">
            Transaction Investigation Log
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Full observability view into Governor request, policy, behavior, provenance & execution decisions
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-[#11161D] px-3 py-1.5 rounded-lg border border-[#232B36]">
          Filtered Total: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-4 flex items-center justify-between gap-4 font-mono text-xs">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search TXN ID, Agent ID, Payee, Category..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full bg-[#171D25] border border-[#232B36] rounded-lg pl-9 pr-3 py-2 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-[#3395FF]"
            />
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-slate-400 flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Decision:</span>
          </span>
          <div className="flex space-x-1 bg-[#171D25] p-1 rounded-lg border border-[#232B36]">
            {["", "ALLOW", "FLAG", "BLOCK"].map((dec) => (
              <button
                key={dec}
                onClick={() => {
                  setDecisionFilter(dec);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded text-[11px] font-bold transition-colors ${
                  decisionFilter === dec
                    ? "bg-[#3395FF] text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {dec || "ALL"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
          ✕ Error: {error}
        </div>
      )}

      {/* Transactions Table */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse bg-[#11161D] h-14 rounded-xl border border-[#232B36]" />
          ))}
        </div>
      ) : transactions.length === 0 ? (
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-12 text-center text-slate-500 font-mono text-xs">
          No transactions found matching criteria.
        </div>
      ) : (
        <div className="bg-[#11161D] border border-[#232B36] rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-[#171D25] text-slate-400 border-b border-[#232B36] uppercase text-[10px] tracking-wider">
                <th className="p-3">Timestamp</th>
                <th className="p-3">Transaction ID</th>
                <th className="p-3">Agent</th>
                <th className="p-3">Amount</th>
                <th className="p-3">Payee / Category</th>
                <th className="p-3">Decision</th>
                <th className="p-3">Execution Gate</th>
                <th className="p-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232B36]">
              {transactions.map((t) => {
                const isAllow = t.decision === "ALLOW";
                const isFlag = t.decision === "FLAG";
                const isBlock = t.decision === "BLOCK";

                return (
                  <tr
                    key={t.txn_id}
                    onClick={() => openInvestigation(t.txn_id)}
                    className="hover:bg-[#171D25]/60 transition-colors cursor-pointer"
                  >
                    <td className="p-3 text-slate-400 text-[11px]">
                      {new Date(t.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3 font-bold text-white">{t.txn_id}</td>
                    <td className="p-3 text-[#3395FF]">{t.agent_id}</td>
                    <td className="p-3 text-emerald-400 font-bold">₹{t.amount_inr}</td>
                    <td className="p-3 text-slate-300">
                      {t.payee_id}
                      <span className="block text-[10px] text-slate-500">{t.category}</span>
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isAllow
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : isFlag
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-red-500/10 text-red-400 border border-red-500/20"
                        }`}
                      >
                        {t.decision}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 text-[11px]">
                      {t.razorpay_payout_id ? (
                        <span className="text-emerald-400 font-bold">{t.razorpay_payout_id}</span>
                      ) : (
                        <span className="text-slate-500">NOT EXECUTED</span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <button className="text-slate-400 hover:text-[#3395FF] p-1">
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination Controls */}
          <div className="bg-[#171D25] p-3 border-t border-[#232B36] flex items-center justify-between font-mono text-xs text-slate-400">
            <span>
              Page {page} of {Math.ceil(total / pageSize) || 1}
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-[#11161D] hover:bg-[#232B36] border border-[#232B36] rounded disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * pageSize >= total}
                className="px-3 py-1 bg-[#11161D] hover:bg-[#232B36] border border-[#232B36] rounded disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Investigation Drawer */}
      {selectedTxnId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-4xl bg-[#0B0F14] border-l border-[#232B36] h-full p-6 overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-[#232B36] pb-4">
              <div>
                <h3 className="text-lg font-bold text-white font-mono">
                  Transaction Pipeline Investigation
                </h3>
                <p className="text-xs text-slate-400 font-mono">
                  {selectedTxnId}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedTxnId(null);
                  setFullTxn(null);
                }}
                className="p-1 rounded hover:bg-[#171D25] text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {fullLoading || !fullTxn ? (
              <div className="p-12 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center space-y-3">
                <RefreshCw className="w-6 h-6 animate-spin text-[#3395FF]" />
                <span>Extracting full Governor decision trace & audit sequence...</span>
              </div>
            ) : (
              <PipelineVisualizer data={fullTxn} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
