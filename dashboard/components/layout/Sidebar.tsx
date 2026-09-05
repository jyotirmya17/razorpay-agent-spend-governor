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
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Agents", href: "/agents", icon: Users },
  { name: "Mandates", href: "/mandates", icon: Shield },
  { name: "Transactions", href: "/transactions", icon: CreditCard },
  { name: "Risk", href: "/risk", icon: AlertTriangle },
  { name: "Audit Trail", href: "/audit", icon: FileCheck },
  { name: "Demo Center", href: "/demo", icon: PlayCircle },
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
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded bg-[#3395FF] flex items-center justify-center text-[#0B0F14] font-extrabold text-xs">
                G
              </div>
              <span className="font-bold text-sm tracking-wider uppercase text-white">
                Governor
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 font-medium">
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
              item.href === "/"
                ? pathname === "/"
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
