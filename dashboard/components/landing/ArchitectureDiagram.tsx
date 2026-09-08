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

    const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.5 });

    // Reset initial states
    gsap.set(dotRef.current, { x: 120 - DOT_RADIUS, y: 175 - DOT_RADIUS, opacity: 1, backgroundColor: "#000000" });
    gsap.set('.step-text', { color: "rgba(0,0,0,0.3)" });
    gsap.set('.step-icon', { opacity: 0.3, color: "#000000" });
    gsap.set('.allow-box', { backgroundColor: "#FDFBF7", color: "#000000" });

    // AGENT -> GOVERNOR STEP 1
    tl.to(dotRef.current, { x: 160 - DOT_RADIUS, duration: 0.25, ease: "none", onStart: () => setCaption("Agent initiates a payout instruction.") })
      .to(dotRef.current, { y: 75 - DOT_RADIUS, duration: 0.35, ease: "none" })
      .to(dotRef.current, { x: 240 - DOT_RADIUS, duration: 0.25, ease: "none" })
      
    // Step 1
    .add(() => {
      setCaption("1. Verifying instruction against cryptographic mandate.");
      gsap.to('#step-1 .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-1 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    .to(dotRef.current, { y: 125 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })
    
    // Step 2
    .add(() => {
      setCaption("2. Applying deterministic spend policies and velocity limits.");
      gsap.to('#step-2 .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-2 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    .to(dotRef.current, { y: 175 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })
    
    // Step 3a
    .add(() => {
      setCaption("3. Scanning for behavioral anomalies and origin tampering.");
      gsap.to('#step-3a .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-3a .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    .to(dotRef.current, { y: 225 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })

    // Step 3b
    .add(() => {
      gsap.to('#step-3b .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-3b .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    .to(dotRef.current, { y: 275 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })

    // Step 4
    .add(() => {
      setCaption("4. Risk Decision Engine evaluating final signal matrix.");
      gsap.to('#step-4 .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-4 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    
    // GOVERNOR -> ALLOW
    .to(dotRef.current, { x: 550 - DOT_RADIUS, duration: 0.6, ease: "none", delay: 0.4 })
    .to(dotRef.current, { y: 175 - DOT_RADIUS, duration: 0.3, ease: "none" })
    .to(dotRef.current, { x: 590 - DOT_RADIUS, duration: 0.15, ease: "none" })

    // ALLOW Decision
    .add(() => {
      setCaption("Decision: ALLOW. Instruction cleared for execution.");
      gsap.to('.allow-box', { backgroundColor: "#22C55E", color: "#FDFBF7", duration: 0.2 });
      gsap.to(dotRef.current, { backgroundColor: "#22C55E", duration: 0.2 });
    })
    
    // ALLOW -> RZX
    .set(dotRef.current, { x: 670 - DOT_RADIUS, delay: 0.5 }) 
    .to(dotRef.current, { x: 760 - DOT_RADIUS, duration: 0.35, ease: "none" })
    .add(() => {
      setCaption("RazorpayX payout successfully initiated.");
    })
    
    // Fade out and loop
    .to(dotRef.current, { opacity: 0, duration: 0.3, delay: 0.8 });

  }, { scope: containerRef });

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center">
      <div 
        ref={containerRef}
        className="relative w-full max-w-[900px] h-[350px] border-2 border-black bg-transparent overflow-hidden hidden md:block shadow-[12px_12px_0_0_#000]"
      >
        {/* SVG PATHS & GRID */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" stroke="rgba(0,0,0,0.15)" strokeWidth="2" fill="none">
          {/* Background grid pattern for technical feel */}
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,0,0,0.03)" strokeWidth="1"/>
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" stroke="none" />

          {/* Data Paths */}
          <path d="M 120 175 L 160 175 L 160 75 L 240 75" />
          <path d="M 240 75 L 240 275" />
          <path d="M 240 275 L 550 275 L 550 175 L 590 175" />
          
          <path d="M 550 175 L 550 100 L 590 100" />
          <path d="M 550 175 L 550 250 L 590 250" />

          <path d="M 670 175 L 760 175" />

          {/* Junction Nodes */}
          <circle cx="160" cy="75" r="3" fill="rgba(0,0,0,0.2)" stroke="none" />
          <circle cx="550" cy="275" r="3" fill="rgba(0,0,0,0.2)" stroke="none" />
          <circle cx="550" cy="175" r="3" fill="rgba(0,0,0,0.2)" stroke="none" />
          <circle cx="550" cy="100" r="3" fill="rgba(0,0,0,0.2)" stroke="none" />
          <circle cx="550" cy="250" r="3" fill="rgba(0,0,0,0.2)" stroke="none" />
          
          {/* Step Nodes */}
          {[75, 125, 175, 225, 275].map(y => (
             <circle key={y} cx="240" cy={y} r="5" fill="#FDFBF7" stroke="rgba(0,0,0,0.3)" strokeWidth="2" />
          ))}
        </svg>

        {/* THE TRAVELING DOT */}
        <div 
          ref={dotRef}
          className="absolute top-0 left-0 w-[12px] h-[12px] bg-black rounded-full z-50 shadow-[0_0_10px_rgba(37,99,235,0.5)]"
        />

        {/* AGENT BOX */}
        <div className="absolute left-[40px] top-[135px] w-[80px] h-[80px] border-2 border-black bg-[#FDFBF7] flex items-center justify-center text-xs font-mono font-bold tracking-widest z-10 text-black shadow-[6px_6px_0_0_#000]">
          AGENT
        </div>

        {/* GOVERNOR BOX */}
        <div className="absolute left-[200px] top-[35px] w-[320px] h-[280px] border-2 border-black bg-[#FDFBF7] z-10 shadow-[8px_8px_0_0_#000] flex flex-col items-start pt-[28px] pl-[60px] space-y-[26px]">
          <div className="absolute -top-[12px] left-[16px] bg-[#FDFBF7] border-2 border-black px-3 py-0.5 text-[10px] font-mono font-bold uppercase tracking-widest text-black">
            Agent Spend Governor
          </div>
          
          <StepItem id="step-1" icon={<CheckCircle2 />} text="Mandate Verification" />
          <StepItem id="step-2" icon={<CheckCircle2 />} text="Deterministic Policy" />
          <StepItem id="step-3a" icon={<Shield />} text="Anomaly Detection" />
          <StepItem id="step-3b" icon={<GitMerge />} text="Origin Provenance" />
          <StepItem id="step-4" icon={<Lock />} text="Risk Decision Engine" />
        </div>

        {/* DECISION BOXES */}
        <div className="allow-box absolute left-[590px] top-[155px] w-[80px] h-[40px] border-2 border-black bg-[#FDFBF7] text-black text-[10px] font-mono font-bold tracking-widest flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000] transition-colors">
          ALLOW
        </div>
        <div className="absolute left-[590px] top-[80px] w-[80px] h-[40px] border-2 border-black bg-[#FDFBF7] text-black text-[10px] font-mono font-bold tracking-widest flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000]">
          FLAG
        </div>
        <div className="absolute left-[590px] top-[230px] w-[80px] h-[40px] border-2 border-black bg-[#FDFBF7] text-black text-[10px] font-mono font-bold tracking-widest flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000]">
          BLOCK
        </div>

        {/* RZX BOX */}
        <div className="absolute left-[760px] top-[135px] w-[80px] h-[80px] border-2 border-black bg-[#FDFBF7] flex items-center justify-center z-10 shadow-[6px_6px_0_0_#000]">
          <span className="text-black font-mono font-bold tracking-widest">RZX</span>
        </div>
      </div>

      {/* MOBILE FALLBACK */}
      <div className="md:hidden border-2 border-black p-6 text-sm text-black font-bold text-center w-full bg-[#FDFBF7] shadow-[6px_6px_0_0_#000]">
        Interactive diagram requires a larger screen.
      </div>

      {/* CAPTION */}
      <div className="mt-12 flex items-center justify-center w-full px-4">
        <p className="text-xs md:text-sm font-mono font-bold text-black bg-[#FDFBF7] border-2 border-black px-6 py-3 shadow-[6px_6px_0_0_#000] tracking-tight">
          {caption}
        </p>
      </div>
    </div>
  );
}

function StepItem({ id, icon, text }: { id: string, icon: React.ReactNode, text: string }) {
  return (
    <div id={id} className="flex items-center text-xs font-mono font-bold text-black transition-colors duration-300">
      <div className="step-icon w-4 h-4 mr-3">
        {icon}
      </div>
      <span className="step-text tracking-tight">{text}</span>
    </div>
  );
}
