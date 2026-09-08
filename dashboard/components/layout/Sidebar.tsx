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
  CheckCircle2,
  XCircle,
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
    <aside className="w-64 bg-[#11161D] border-r border-[#232B36] flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-[#232B36] flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2.5">
              <svg className="w-6 h-6 text-[#3395FF]" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="32" height="32" rx="7" fill="#3395FF" fillOpacity="0.12" stroke="#3395FF" strokeOpacity="0.3" strokeWidth="1.5" />
                <path d="M21 11.5H13.5C12.1193 11.5 11 12.6193 11 14V18C11 19.3807 12.1193 20.5 13.5 20.5H19.5C20.8807 20.5 22 19.3807 22 18V15.5H16.5" stroke="#3395FF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="font-bold text-sm tracking-wider uppercase text-white font-mono">
                Governor
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 font-medium font-mono">
              Agent Spend Governor
            </p>
          </div>
          <span className="text-[10px] uppercase font-mono tracking-widest px-1.5 py-0.5 rounded bg-blue-500/10 text-[#3395FF] border border-blue-500/20">
            v1.0
          </span>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
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
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#3395FF]/10 text-[#3395FF] border border-[#3395FF]/20"
                    : "text-slate-400 hover:text-white hover:bg-[#171D25]"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#3395FF]" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* System Health / Footer */}
      <div className="p-4 border-t border-[#232B36] bg-[#0B0F14]/50 space-y-3">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400 font-medium">System Status</span>
          <span
            className={`flex items-center space-x-1 font-semibold ${
              isHealthy ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full animate-pulse ${
                isHealthy ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            <span className="uppercase text-[10px]">{health?.status || "Connecting..."}</span>
          </span>
        </div>

        <div className="space-y-1.5 text-[10px] font-mono text-slate-400">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <Activity className="w-3 h-3 text-slate-500" />
              <span>API</span>
            </span>
            <span className="text-emerald-400 font-bold">ONLINE</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <Database className="w-3 h-3 text-slate-500" />
              <span>POSTGRESQL</span>
            </span>
            <span className="text-emerald-400 font-bold">
              {health?.components?.postgres?.status?.toUpperCase() || "OK"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <Lock className="w-3 h-3 text-slate-500" />
              <span>AUDIT CHAIN</span>
            </span>
            <span className="text-emerald-400 font-bold">
              {health?.components?.audit_chain?.valid ? "VALID" : "CHECKING"}
            </span>
          </div>
        </div>

        <div className="pt-2 border-t border-[#232B36]/60">
          <div className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded text-[10px] text-[#3395FF] font-mono text-center font-bold tracking-wider uppercase">
            RAZORPAYX TEST MODE
          </div>
        </div>
      </div>
    </aside>
  );
}
