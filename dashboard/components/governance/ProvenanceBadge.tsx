import { SourceTrust } from "@/lib/types";
import { ShieldCheck, ShieldAlert, HelpCircle } from "lucide-react";

interface ProvenanceBadgeProps {
  trust: SourceTrust | string | null | undefined;
  origin?: string | null;
  size?: "sm" | "md";
}

export function ProvenanceBadge({ trust, origin, size = "md" }: ProvenanceBadgeProps) {
  const normalizedTrust = (trust || "UNKNOWN").toUpperCase();

  let colorClass = "bg-[#FDFBF7] text-gray-600 border-gray-500 shadow-[2px_2px_0_0_#6b7280]";
  let icon = <HelpCircle className={size === "sm" ? "w-3 h-3" : "w-4 h-4"} />;
  let label = "UNKNOWN";

  if (normalizedTrust === "TRUSTED") {
    colorClass = "bg-[#FDFBF7] text-green-600 border-green-500 shadow-[2px_2px_0_0_#22c55e]";
    icon = <ShieldCheck className={size === "sm" ? "w-3 h-3" : "w-4 h-4"} />;
    label = "TRUSTED";
  } else if (normalizedTrust === "UNTRUSTED") {
    colorClass = "bg-[#FDFBF7] text-amber-600 border-amber-500 shadow-[2px_2px_0_0_#f59e0b]";
    icon = <ShieldAlert className={size === "sm" ? "w-3 h-3" : "w-4 h-4"} />;
    label = "UNTRUSTED";
  }

  const isSmall = size === "sm";

  return (
    <div
      className={`inline-flex items-center space-x-2 font-mono border-2 font-bold uppercase tracking-widest ${colorClass} ${
        isSmall ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-xs"
      }`}
    >
      {icon}
      <span>{label}</span>
      {origin && <span className="opacity-60 text-[9px] ml-1">({origin})</span>}
    </div>
  );
}
