import { AuditEventItem } from "@/lib/types";
import { ArrowDown, Hash, Clock, FileText } from "lucide-react";

interface AuditChainViewerProps {
  events: AuditEventItem[];
}

export function AuditChainViewer({ events }: AuditChainViewerProps) {
  if (!events || events.length === 0) {
    return (
      <div className="bg-[#11161D] border border-[#232B36] rounded-xl p-8 text-center text-slate-400 font-mono text-xs">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Banner */}
      <div className="flex items-center justify-between px-2 font-mono text-xs text-slate-400">
        <span>SHOWING LATEST AUDIT EVENTS (ORDERED BY SEQUENCE DESC)</span>
        <span>TOTAL SHOWN: {events.length}</span>
      </div>

      <div className="space-y-3 font-mono">
        {events.map((ev, idx) => (
          <div key={ev.event_id} className="relative">
            <div className="bg-[#11161D] border border-[#232B36] hover:border-[#3395FF]/40 transition-colors rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-[#232B36] pb-2.5">
                <div className="flex items-center space-x-3">
                  <span className="px-2 py-0.5 rounded bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20 text-xs font-bold">
                    SEQ #{ev.sequence_id}
                  </span>
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    {ev.event_type}
                  </span>
                </div>

                <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{new Date(ev.timestamp).toLocaleString()}</span>
                  </span>
                  <span className="text-slate-500">Entity: <strong className="text-slate-300">{ev.entity_id}</strong></span>
                </div>
              </div>

              {/* Hash Cryptographic Link */}
              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="bg-[#171D25] p-2.5 rounded border border-[#232B36]">
                  <span className="text-slate-500 block text-[9px] uppercase tracking-wider mb-0.5">
                    PREVIOUS EVENT HASH
                  </span>
                  <p className="font-mono text-slate-400 break-all text-[10px]">
                    {ev.previous_event_hash}
                  </p>
                </div>

                <div className="bg-[#171D25] p-2.5 rounded border border-[#232B36]">
                  <span className="text-slate-500 block text-[9px] uppercase tracking-wider mb-0.5">
                    CURRENT EVENT HASH (SHA-256)
                  </span>
                  <p className="font-mono text-emerald-400 font-bold break-all text-[10px]">
                    {ev.event_hash}
                  </p>
                </div>
              </div>
            </div>

            {/* Link arrow between events */}
            {idx < events.length - 1 && (
              <div className="flex justify-center my-1">
                <div className="w-0.5 h-3 bg-[#232B36]" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
