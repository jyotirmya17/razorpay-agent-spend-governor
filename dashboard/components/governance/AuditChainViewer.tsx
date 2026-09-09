import { AuditEventItem } from "@/lib/types";
import { Clock } from "lucide-react";
import { parseUtcTimestamp } from "@/lib/utils";

interface AuditChainViewerProps {
  events: AuditEventItem[];
}

export function AuditChainViewer({ events }: AuditChainViewerProps) {
  if (!events || events.length === 0) {
    return (
      <div className="bg-[#FDFBF7] border-2 border-black border-dashed p-8 text-center text-black font-mono text-xs font-bold uppercase tracking-widest">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Banner */}
      <div className="flex items-center justify-between px-2 font-mono text-xs text-black font-bold uppercase tracking-widest">
        <span className="bg-black/5 px-2 py-1 border-2 border-black">SHOWING LATEST AUDIT EVENTS (ORDERED BY SEQUENCE DESC)</span>
        <span className="bg-black/5 px-2 py-1 border-2 border-black">TOTAL SHOWN: {events.length}</span>
      </div>

      <div className="space-y-4 font-mono">
        {events.map((ev, idx) => (
          <div key={ev.event_id} className="relative">
            <div className="bg-[#FDFBF7] border-2 border-black shadow-[4px_4px_0_0_#000] p-5 space-y-4 hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#000] transition-all">
              <div className="flex items-center justify-between border-b-2 border-black pb-3">
                <div className="flex items-center space-x-4">
                  <span className="px-3 py-1 bg-black text-[#FDFBF7] border-2 border-black text-xs font-bold uppercase tracking-widest shadow-[2px_2px_0_0_#000]">
                    SEQ #{ev.sequence_id}
                  </span>
                  <span className="text-xs font-bold text-black uppercase tracking-widest">
                    {ev.event_type}
                  </span>
                </div>

                <div className="flex items-center space-x-6 text-[11px] text-black font-bold uppercase tracking-widest">
                  <span className="flex items-center space-x-2">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{parseUtcTimestamp(ev.timestamp).toLocaleString()}</span>
                  </span>
                  <span>Entity: <strong className="underline underline-offset-4 decoration-black/30">{ev.entity_id}</strong></span>
                </div>
              </div>

              {/* Hash Cryptographic Link */}
              <div className="grid grid-cols-2 gap-4 text-[11px] font-bold uppercase tracking-widest">
                <div className="bg-black/5 p-4 border-2 border-black shadow-[2px_2px_0_0_#000]">
                  <span className="text-black/60 block text-[10px] mb-2 border-b-2 border-black/10 pb-1">
                    PREVIOUS EVENT HASH
                  </span>
                  <p className="font-mono text-black break-all text-[10px] leading-relaxed">
                    {ev.previous_event_hash}
                  </p>
                </div>

                <div className="bg-[#FDFBF7] p-4 border-2 border-black shadow-[2px_2px_0_0_#000]">
                  <span className="text-black block text-[10px] mb-2 border-b-2 border-black pb-1">
                    CURRENT EVENT HASH (SHA-256)
                  </span>
                  <p className="font-mono text-green-600 break-all text-[10px] leading-relaxed">
                    {ev.event_hash}
                  </p>
                </div>
              </div>
            </div>

            {/* Link arrow between events */}
            {idx < events.length - 1 && (
              <div className="flex justify-center my-2">
                <div className="w-1 h-6 bg-black" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
