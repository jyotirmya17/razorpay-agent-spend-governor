"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Users,
  Shield,
  CreditCard,
  AlertTriangle,
  FileCheck,
  PlayCircle,
  Activity,
  Database,
  Lock,
} from "lucide-react";
import { api } from "@/lib/api";
import { SystemHealth } from "@/lib/types";

const NAV_ITEMS = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Agents", href: "/dashboard/agents", icon: Users },
  { name: "Mandates", href: "/dashboard/mandates", icon: Shield },
  { name: "Transactions", href: "/dashboard/transactions", icon: CreditCard },
  { name: "Risk", href: "/dashboard/risk", icon: AlertTriangle },
  { name: "Audit Trail", href: "/dashboard/audit", icon: FileCheck },
  { name: "Governance Scenarios", href: "/dashboard/demo", icon: PlayCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        const data = await api.getHealth();
        if (active) setHealth(data);
      } catch {
        if (active) setHealth(null);
      }
    };
    check();
    const timer = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const isHealthy = health?.status === "healthy" || health?.status === "ready";

  return (
    <aside className="w-64 bg-[#FDFBF7] border-r-2 border-black flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b-2 border-black flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="w-6 h-6 border-2 border-black shadow-[2px_2px_0_0_#000] flex items-center justify-center bg-black">
                <Shield className="w-3.5 h-3.5 text-[#FDFBF7]" />
              </div>
              <span className="font-bold text-sm tracking-wider uppercase text-black font-mono">
                Governor
              </span>
            </div>
            <p className="text-[10px] text-black/60 mt-1.5 font-bold font-mono tracking-widest uppercase">
              Agent Spend Control
            </p>
          </div>
          <span className="text-[10px] font-bold font-mono tracking-widest px-1.5 py-0.5 border-2 border-black shadow-[2px_2px_0_0_#000] bg-black text-[#FDFBF7]">
            V1.0
          </span>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard" || pathname === "/dashboard/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-3 border-2 transition-all font-mono font-bold tracking-tight text-xs uppercase ${
                  isActive
                    ? "border-black bg-black text-[#FDFBF7] shadow-[4px_4px_0_0_#000]"
                    : "border-transparent text-black hover:border-black hover:shadow-[4px_4px_0_0_#000]"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#FDFBF7]" : "text-black"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* System Health / Footer */}
      <div className="p-4 border-t-2 border-black bg-black/5 space-y-4">
        <div className="flex items-center justify-between text-[11px] font-mono font-bold tracking-widest uppercase">
          <span className="text-black">System Status</span>
          <span
            className={`flex items-center space-x-1 border-2 border-black px-1.5 py-0.5 shadow-[2px_2px_0_0_#000] bg-[#FDFBF7] ${
              isHealthy ? "text-green-600" : "text-amber-600"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                isHealthy ? "bg-green-600" : "bg-amber-600"
              }`}
            />
            <span className="text-[9px]">{health?.status || "CONNECTING"}</span>
          </span>
        </div>

        <div className="space-y-2 text-[10px] font-mono text-black font-bold tracking-widest uppercase">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <Activity className="w-3 h-3 text-black" />
              <span>API</span>
            </span>
            <span className="text-green-600">ONLINE</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <Database className="w-3 h-3 text-black" />
              <span>POSTGRES</span>
            </span>
            <span className="text-green-600">
              {health?.components?.postgres?.status?.toUpperCase() || "OK"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <Lock className="w-3 h-3 text-black" />
              <span>AUDIT CHAIN</span>
            </span>
            <span className="text-green-600">
              {health?.components?.audit_chain?.valid ? "VALID" : "SYNCING"}
            </span>
          </div>
        </div>

        <div className="pt-3 border-t-2 border-black">
          <div className="px-2 py-2 border-2 border-black bg-black text-[#FDFBF7] text-[10px] font-mono font-bold tracking-widest uppercase text-center shadow-[2px_2px_0_0_#000]">
            RAZORPAYX TEST MODE
          </div>
        </div>
      </div>
    </aside>
  );
}
