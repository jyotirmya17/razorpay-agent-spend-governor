import { SourceTrust } from "@/lib/types";
import { ShieldCheck, ShieldAlert, HelpCircle } from "lucide-react";

interface ProvenanceBadgeProps {
  trust: SourceTrust | string | null | undefined;
  origin?: string | null;
  size?: "sm" | "md";
}

export function ProvenanceBadge({ trust, origin, size = "md" }: ProvenanceBadgeProps) {
  const normalizedTrust = (trust || "UNKNOWN").toUpperCase();

  let colorClass = "bg-gray-500/10 text-gray-400 border-gray-500/20";
  let icon = <HelpCircle className={size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"} />;
  let label = "UNKNOWN";

  if (normalizedTrust === "TRUSTED") {
    colorClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    icon = <ShieldCheck className={size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"} />;
    label = "TRUSTED";
  } else if (normalizedTrust === "UNTRUSTED") {
    colorClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
    icon = <ShieldAlert className={size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"} />;
    label = "UNTRUSTED";
  }

  const isSmall = size === "sm";

  return (
    <div
      className={`inline-flex items-center space-x-1.5 font-mono rounded border font-semibold ${colorClass} ${
        isSmall ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs"
      }`}
    >
      {icon}
      <span>{label}</span>
      {origin && <span className="opacity-60 text-[9px]">({origin})</span>}
    </div>
  );
}
