"use client";

import { useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { CheckCircle2, Shield, GitMerge, Lock } from "lucide-react";

gsap.registerPlugin(useGSAP);

const DOT_RADIUS = 6;

export default function ArchitectureDiagram() {
  const containerRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);
  const [caption, setCaption] = useState("Agent initiates a payout instruction.");

  useGSAP(() => {
    if (!dotRef.current) return;

    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1 });

    const step = (x: number, y: number, text: string, delay = 0) => {
      tl.to(dotRef.current, {
        x: x - DOT_RADIUS,
        y: y - DOT_RADIUS,
        duration: 0.6,
        ease: "power2.inOut",
        onStart: () => setCaption(text),
      }, `+=${delay}`);
    };

    gsap.set(dotRef.current, { x: 80 - DOT_RADIUS, y: 150 - DOT_RADIUS, opacity: 1 });

    step(250, 60, "1. Verifying instruction against cryptographic mandate.", 0.5);
    step(250, 105, "2. Applying deterministic spend policies and velocity limits.", 0.5);
    step(250, 150, "3. Scanning for behavioral anomalies and origin tampering.", 0.5);
    step(250, 195, "4. Risk Decision Engine evaluating final signal matrix.", 0.5);
    step(250, 240, "5. Committing tamper-evident hash to the audit chain.", 0.5);
    step(590, 100, "Decision: ALLOW. Instruction cleared for execution.", 0.5);
    step(780, 150, "RazorpayX payout successfully initiated.", 0.5);

    tl.to(dotRef.current, { opacity: 0, duration: 0.3 }, "+=1");
    tl.set(dotRef.current, { x: 80 - DOT_RADIUS, y: 150 - DOT_RADIUS });
    tl.to(dotRef.current, { opacity: 1, duration: 0.3, onStart: () => setCaption("Agent initiates a new payout instruction.") });

  }, { scope: containerRef });

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center">
      <div 
        ref={containerRef}
        className="relative w-full max-w-[900px] h-[300px] border-2 border-black bg-transparent overflow-hidden hidden md:block shadow-[8px_8px_0_0_#000]"
      >
        <svg className="absolute inset-0 w-full h-full pointer-events-none" stroke="rgba(0,0,0,0.3)" strokeWidth="2" fill="none">
          <path d="M 120 150 L 250 60" />
          <path d="M 120 150 L 250 105" />
          <path d="M 120 150 L 250 150" />
          <path d="M 120 150 L 250 195" />
          <path d="M 120 150 L 250 240" />
          
          <path d="M 550 150 L 590 100" />
          <path d="M 550 150 L 590 150" />
          <path d="M 550 150 L 590 200" />

          <path d="M 680 100 L 780 150" />
        </svg>

        <div 
          ref={dotRef}
          className="absolute top-0 left-0 w-[14px] h-[14px] bg-black rounded-full z-50"
        />

        <div className="absolute left-[40px] top-[110px] w-[80px] h-[80px] border-2 border-black bg-white flex items-center justify-center text-xs font-mono font-bold tracking-widest z-10 text-black shadow-[4px_4px_0_0_#000]">
          AGENT
        </div>

        <div className="absolute left-[250px] top-[20px] w-[300px] h-[260px] border-2 border-black bg-black p-4 flex flex-col justify-between z-10 shadow-[6px_6px_0_0_#000]">
          <div className="text-[10px] text-white/50 uppercase tracking-widest font-mono font-bold absolute -top-[12px] left-4 bg-black px-2">Agent Spend Governor</div>
          
          <div className="flex items-center text-xs text-white/90 font-medium h-8">
            <CheckCircle2 className="w-4 h-4 mr-3 text-white/30" /> <span className="font-mono mr-2 text-white/50">1.</span> Mandate Verification
          </div>
          <div className="flex items-center text-xs text-white/90 font-medium h-8">
            <CheckCircle2 className="w-4 h-4 mr-3 text-white/30" /> <span className="font-mono mr-2 text-white/50">2.</span> Deterministic Policy
          </div>
          <div className="flex items-center text-xs text-white/90 font-medium h-8">
            <Shield className="w-4 h-4 mr-3 text-[#FDE68A]" /> <span className="font-mono mr-2 text-white/50">3a.</span> Anomaly Detection
          </div>
          <div className="flex items-center text-xs text-white/90 font-medium h-8">
            <GitMerge className="w-4 h-4 mr-3 text-[#FDE68A]" /> <span className="font-mono mr-2 text-white/50">3b.</span> Origin Provenance
          </div>
          <div className="flex items-center text-xs text-white/90 font-medium h-8">
            <Lock className="w-4 h-4 mr-3 text-white/30" /> <span className="font-mono mr-2 text-white/50">4.</span> Risk Decision Engine
          </div>
        </div>

        <div className="absolute left-[590px] top-[85px] px-3 py-1.5 border-2 border-black text-black bg-[#22C55E] text-[10px] font-mono font-bold tracking-widest z-10 shadow-[3px_3px_0_0_#000]">ALLOW</div>
        <div className="absolute left-[590px] top-[135px] px-3 py-1.5 border-2 border-black text-black bg-white text-[10px] font-mono font-bold tracking-widest z-10 shadow-[3px_3px_0_0_#000]">FLAG</div>
        <div className="absolute left-[590px] top-[185px] px-3 py-1.5 border-2 border-black text-white bg-[#EF4444] text-[10px] font-mono font-bold tracking-widest z-10 shadow-[3px_3px_0_0_#000]">BLOCK</div>

        <div className="absolute left-[780px] top-[110px] w-[80px] h-[80px] border-2 border-black bg-white flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000]">
          <span className="text-black font-mono font-bold tracking-widest">RZX</span>
        </div>
      </div>

      <div className="md:hidden border-2 border-black p-6 text-sm text-black font-bold text-center w-full bg-white shadow-[6px_6px_0_0_#000]">
        Interactive diagram requires a larger screen.
      </div>

      <div className="mt-8 h-12 flex items-center justify-center w-full px-4 text-center">
        <p className="text-sm font-mono font-bold text-black opacity-80">{caption}</p>
      </div>
    </div>
  );
}
