"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { TransactionSummary, FullTransactionInvestigation } from "@/lib/types";
import { PipelineVisualizer } from "@/components/governance/PipelineVisualizer";
import { parseUtcTimestamp } from "@/lib/utils";
import {
  Search,
  Filter,
  ChevronRight,
  X,
  RefreshCw,
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
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b-2 border-black pb-4">
        <div>
          <h2 className="text-xl font-bold text-black font-mono tracking-tight uppercase">
            Transaction Investigation Log
          </h2>
          <p className="text-xs text-black/60 font-mono mt-1 font-bold tracking-widest uppercase">
            Full observability view into execution decisions
          </p>
        </div>
        <span className="text-xs font-mono font-bold tracking-widest text-black bg-[#FDFBF7] px-4 py-2 border-2 border-black shadow-[4px_4px_0_0_#000] uppercase">
          Filtered Total: <strong className="text-black ml-2">{total}</strong>
        </span>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-[#FDFBF7] border-2 border-black shadow-[6px_6px_0_0_#000] p-4 flex items-center justify-between gap-4 font-mono font-bold uppercase tracking-widest text-xs">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-black absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search TXN ID, Agent, Payee..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full bg-[#FDFBF7] border-2 border-black p-2 pl-9 text-black placeholder-black/40 text-xs focus:outline-none focus:ring-0 focus:shadow-[2px_2px_0_0_#000] transition-shadow uppercase font-bold"
            />
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-black flex items-center space-x-1">
            <Filter className="w-4 h-4" />
            <span>Decision:</span>
          </span>
          <div className="flex space-x-2">
            {["", "ALLOW", "REVIEW", "DENY"].map((dec) => (
              <button
                key={dec}
                onClick={() => {
                  setDecisionFilter(dec);
                  setPage(1);
                }}
                className={`px-3 py-1.5 border-2 border-black transition-all shadow-[2px_2px_0_0_#000] hover:shadow-none hover:translate-y-0.5 ${
                  decisionFilter === dec
                    ? "bg-black text-[#FDFBF7]"
                    : "bg-[#FDFBF7] text-black hover:bg-black hover:text-[#FDFBF7]"
                }`}
              >
                {dec || "ALL"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-[#FDFBF7] text-red-600 border-2 border-red-500 shadow-[4px_4px_0_0_#ef4444] text-xs font-mono font-bold uppercase tracking-widest">
          ✕ Error: {error}
        </div>
      )}

      {/* Transactions Table */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse bg-[#FDFBF7] h-14 border-2 border-black shadow-[4px_4px_0_0_#000]" />
          ))}
        </div>
      ) : transactions.length === 0 ? (
        <div className="bg-[#FDFBF7] border-2 border-black p-12 text-center text-black font-mono font-bold uppercase tracking-widest text-xs border-dashed">
          No transactions found matching criteria.
        </div>
      ) : (
        <div className="bg-[#FDFBF7] border-2 border-black shadow-[8px_8px_0_0_#000] overflow-hidden">
          <table className="w-full text-left border-collapse text-xs font-mono font-bold uppercase tracking-widest">
            <thead>
              <tr className="bg-black text-[#FDFBF7] border-b-2 border-black text-[10px]">
                <th className="p-4">Timestamp</th>
                <th className="p-4">Transaction ID</th>
                <th className="p-4">Agent</th>
                <th className="p-4">Amount</th>
                <th className="p-4">Payee / Category</th>
                <th className="p-4">Decision</th>
                <th className="p-4">Execution Gate</th>
                <th className="p-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-black text-black">
              {transactions.map((t) => {
                const isAllow = t.decision === "ALLOW" || t.decision === "SUCCEEDED";
                const isFlag = t.decision === "REVIEW";

                return (
                  <tr
                    key={t.txn_id}
                    onClick={() => openInvestigation(t.txn_id)}
                    className="hover:bg-black/5 transition-colors cursor-pointer"
                  >
                    <td className="p-4 text-black/60 text-[10px]">
                      {parseUtcTimestamp(t.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-4 text-black">{t.txn_id}</td>
                    <td className="p-4 text-black underline underline-offset-4 decoration-black/30">{t.agent_id}</td>
                    <td className="p-4 text-black">₹{t.amount_inr}</td>
                    <td className="p-4 text-black">
                      {t.payee_id}
                      <span className="block text-[10px] text-black/60 mt-1">{t.category}</span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-1 text-[10px] border-2 shadow-[2px_2px_0_0_#000] inline-block ${
                          isAllow
                            ? "border-green-500 text-green-600 bg-[#FDFBF7]"
                            : isFlag
                            ? "border-amber-500 text-amber-600 bg-[#FDFBF7]"
                            : "border-red-500 text-red-600 bg-[#FDFBF7]"
                        }`}
                      >
                        {t.decision}
                      </span>
                    </td>
                    <td className="p-4 text-[10px]">
                      {t.razorpay_payout_id ? (
                        <span className="text-black bg-black/5 px-2 py-1 border-2 border-black">{t.razorpay_payout_id}</span>
                      ) : (
                        <span className="text-black/40">NOT EXECUTED</span>
                      )}
                    </td>
                    <td className="p-4 text-right">
                      <button className="text-black hover:text-[#FDFBF7] hover:bg-black p-1 border-2 border-transparent hover:border-black transition-colors">
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination Controls */}
          <div className="bg-[#FDFBF7] p-4 border-t-2 border-black flex items-center justify-between font-mono font-bold uppercase tracking-widest text-xs text-black">
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

      {/* Pipeline Investigation Drawer */}
      {selectedTxnId && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-5xl bg-[#FDFBF7] border-l-4 border-black h-full p-8 overflow-y-auto space-y-8 font-mono shadow-[-12px_0_0_0_rgba(0,0,0,1)]">
            <div className="flex items-center justify-between border-b-4 border-black pb-6">
              <div>
                <h3 className="text-xl font-bold text-black uppercase">
                  Transaction Pipeline Investigation
                </h3>
                <p className="text-xs text-black/60 font-bold tracking-widest mt-1">
                  {selectedTxnId}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedTxnId(null);
                  setFullTxn(null);
                }}
                className="p-2 bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] text-black hover:bg-black hover:text-[#FDFBF7] hover:translate-y-1 hover:shadow-none transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {fullLoading || !fullTxn ? (
              <div className="p-16 text-center text-black font-bold uppercase text-xs border-2 border-dashed border-black flex flex-col items-center justify-center space-y-4">
                <RefreshCw className="w-8 h-8 animate-spin" />
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
