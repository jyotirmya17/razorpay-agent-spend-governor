"use client";

import { useRef, useState, useEffect } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { CheckCircle2, Shield, GitMerge, Lock, Play, AlertTriangle, Ban } from "lucide-react";

gsap.registerPlugin(useGSAP);

const DOT_RADIUS = 6;

type ScenarioId = 'clean' | 'spoofed' | 'velocity';

export default function ArchitectureDiagram() {
  const containerRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);
  const [caption, setCaption] = useState("Select a test scenario below to initiate the deterministic Governor pipeline.");
  const [activeScenario, setActiveScenario] = useState<ScenarioId | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Expose play function to our buttons using contextSafe
  const { contextSafe } = useGSAP({ scope: containerRef });

  // Initial setup state
  useGSAP(() => {
    if (dotRef.current) {
      gsap.set(dotRef.current, { opacity: 0 });
    }
  }, { scope: containerRef });

  const runScenario = contextSafe((scenario: ScenarioId) => {
    if (isPlaying) return;
    setIsPlaying(true);
    setActiveScenario(scenario);

    // Ensure GSAP kills any lingering animations on the dot or elements
    gsap.killTweensOf([dotRef.current, '.step-text', '.step-icon', '.allow-box', '.flag-box', '.block-box']);

    const tl = gsap.timeline({ 
      onComplete: () => {
        setTimeout(() => {
          setIsPlaying(false);
          setActiveScenario(null);
        }, 1500); // Give user time to read final state before unlocking
      }
    });

    // Reset initial states for fresh run
    gsap.set(dotRef.current, { x: 120 - DOT_RADIUS, y: 175 - DOT_RADIUS, opacity: 1, backgroundColor: "#000000" });
    gsap.set('.step-text', { color: "rgba(0,0,0,0.3)" });
    gsap.set('.step-icon', { opacity: 0.3, color: "#000000" });
    gsap.set('.allow-box', { backgroundColor: "#FDFBF7", color: "#000000" });
    gsap.set('.flag-box', { backgroundColor: "#FDFBF7", color: "#000000" });
    gsap.set('.block-box', { backgroundColor: "#FDFBF7", color: "#000000" });

    // AGENT -> GOVERNOR STEP 1
    tl.to(dotRef.current, { x: 160 - DOT_RADIUS, duration: 0.25, ease: "none", onStart: () => setCaption("Agent initiates payload transmission.") })
      .to(dotRef.current, { y: 75 - DOT_RADIUS, duration: 0.35, ease: "none" })
      .to(dotRef.current, { x: 240 - DOT_RADIUS, duration: 0.25, ease: "none" })
      
    // Step 1: Mandate Verification
    .add(() => {
      setCaption("1. Cryptographic Mandate: Ed25519 signature verified.");
      gsap.to('#step-1 .step-text', { color: "#000000", duration: 0.2 });
      gsap.to('#step-1 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
    })
    .to(dotRef.current, { y: 125 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })
    
    // Step 2: Deterministic Policy
    .add(() => {
      if (scenario === 'velocity') {
        setCaption("2. POLICY VIOLATION: $5,000 daily limit exceeded. 3rd transaction today.");
        gsap.to('#step-2 .step-text', { color: "#EAB308", duration: 0.2 });
        gsap.to('#step-2 .step-icon', { opacity: 1, color: "#EAB308", duration: 0.2 });
        gsap.to(dotRef.current, { backgroundColor: "#EAB308", duration: 0.2 });
      } else {
        setCaption("2. Deterministic Policy: $5,000 daily vendor limit respected.");
        gsap.to('#step-2 .step-text', { color: "#000000", duration: 0.2 });
        gsap.to('#step-2 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
      }
    })
    .to(dotRef.current, { y: 175 - DOT_RADIUS, duration: 0.4, ease: "none", delay: (scenario === 'velocity') ? 1.0 : 0.3 })
    
    // Step 3a: Anomaly Detection
    .add(() => {
      if (scenario === 'spoofed') {
        setCaption("3. Behavioral Anomaly: Minor timing mismatch detected.");
        gsap.to('#step-3a .step-text', { color: "#EAB308", duration: 0.2 }); // Warn
        gsap.to('#step-3a .step-icon', { opacity: 1, color: "#EAB308", duration: 0.2 });
        gsap.to(dotRef.current, { backgroundColor: "#EAB308", duration: 0.2 });
      } else {
        setCaption("3. Behavioral Anomaly: Transaction velocity is normal.");
        gsap.to('#step-3a .step-text', { color: "#000000", duration: 0.2 });
        gsap.to('#step-3a .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
      }
    })
    .to(dotRef.current, { y: 225 - DOT_RADIUS, duration: 0.4, ease: "none", delay: 0.3 })

    // Step 3b: Origin Provenance
    .add(() => {
      if (scenario === 'spoofed') {
        setCaption("4. FATAL ORIGIN: Payload did not originate from authorized internal AWS VPC.");
        gsap.to('#step-3b .step-text', { color: "#EF4444", duration: 0.2 });
        gsap.to('#step-3b .step-icon', { opacity: 1, color: "#EF4444", duration: 0.2 });
        gsap.to(dotRef.current, { backgroundColor: "#EF4444", duration: 0.2 });
      } else {
        setCaption("4. Origin Provenance: Execution verified within AWS Nitro Enclave.");
        gsap.to('#step-3b .step-text', { color: "#000000", duration: 0.2 });
        gsap.to('#step-3b .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
      }
    })
    .to(dotRef.current, { y: 275 - DOT_RADIUS, duration: 0.4, ease: "none", delay: (scenario === 'spoofed') ? 1.0 : 0.3 })

    // Step 4: Risk Decision Engine
    .add(() => {
      if (scenario === 'velocity') {
        setCaption("5. Risk Engine: Policy limit exceeded. Trust score compromised. Routing to human review.");
        gsap.to('#step-4 .step-text', { color: "#EAB308", duration: 0.2 });
        gsap.to('#step-4 .step-icon', { opacity: 1, color: "#EAB308", duration: 0.2 });
      } else if (scenario === 'spoofed') {
        setCaption("5. Risk Engine: SEVERE COMPROMISE. Origin hijacked. Initiating immediate lock.");
        gsap.to('#step-4 .step-text', { color: "#EF4444", duration: 0.2 });
        gsap.to('#step-4 .step-icon', { opacity: 1, color: "#EF4444", duration: 0.2 });
      } else {
        setCaption("5. Risk Engine: No anomalies detected. Trust score 99%. Cleared.");
        gsap.to('#step-4 .step-text', { color: "#000000", duration: 0.2 });
        gsap.to('#step-4 .step-icon', { opacity: 1, color: "#2563EB", duration: 0.2 });
      }
    })
    
    // GOVERNOR -> DECISION
    .to(dotRef.current, { x: 550 - DOT_RADIUS, duration: 0.6, ease: "none", delay: 0.6 })
    .to(dotRef.current, { 
      y: (scenario === 'velocity' ? 100 : (scenario === 'spoofed' ? 250 : 175)) - DOT_RADIUS, 
      duration: 0.3, ease: "none" 
    })
    .to(dotRef.current, { x: 590 - DOT_RADIUS, duration: 0.15, ease: "none" })

    // DECISION GATES
    .add(() => {
      if (scenario === 'clean') {
        setCaption("Decision: ALLOW. All programmatic rules satisfied.");
        gsap.to('.allow-box', { backgroundColor: "#22C55E", color: "#FDFBF7", duration: 0.2 });
        gsap.to(dotRef.current, { backgroundColor: "#22C55E", duration: 0.2 });
      } else if (scenario === 'velocity') {
        setCaption("Decision: FLAG. Transaction quarantined for Maker-Checker review.");
        gsap.to('.flag-box', { backgroundColor: "#EAB308", color: "#000000", duration: 0.2 });
        gsap.to(dotRef.current, { opacity: 0, duration: 0.2 }); // Dot terminates in flag box
      } else {
        setCaption("Decision: BLOCK. Transaction terminated. Threat logged to tamper-evident chain.");
        gsap.to('.block-box', { backgroundColor: "#EF4444", color: "#FDFBF7", duration: 0.2 });
        gsap.to(dotRef.current, { opacity: 0, duration: 0.2 }); // Dot terminates in block box
      }
    });
    
    // ONLY CLEAN SCENARIO GOES TO RZX
    if (scenario === 'clean') {
      tl.set(dotRef.current, { x: 670 - DOT_RADIUS, delay: 0.5 }) 
        .to(dotRef.current, { x: 760 - DOT_RADIUS, duration: 0.35, ease: "none" })
        .add(() => {
          setCaption("RazorpayX payout successfully initiated via API.");
        })
        .to(dotRef.current, { opacity: 0, duration: 0.3, delay: 0.8 });
    }
  });

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center">
      {/* 1. SCENARIO CONTROLS */}
      <div className="mb-12 flex flex-col sm:flex-row gap-4 w-full justify-center px-4 z-20">
        <button 
          onClick={() => runScenario('clean')}
          disabled={isPlaying}
          className={`flex items-center justify-center space-x-2 px-6 py-4 border-2 border-black font-mono font-bold text-xs uppercase tracking-widest transition-all ${
            activeScenario === 'clean' 
              ? 'bg-[#22C55E] text-[#FDFBF7] shadow-[6px_6px_0_0_#000]' 
              : 'bg-[#FDFBF7] text-black hover:bg-black/5 shadow-[4px_4px_0_0_#000] disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          <Play className="w-4 h-4" />
          <span>Test: Clean Payout</span>
        </button>

        <button 
          onClick={() => runScenario('spoofed')}
          disabled={isPlaying}
          className={`flex items-center justify-center space-x-2 px-6 py-4 border-2 border-black font-mono font-bold text-xs uppercase tracking-widest transition-all ${
            activeScenario === 'spoofed' 
              ? 'bg-[#EF4444] text-[#FDFBF7] shadow-[6px_6px_0_0_#000]' 
              : 'bg-[#FDFBF7] text-black hover:bg-black/5 shadow-[4px_4px_0_0_#000] disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          <Ban className="w-4 h-4" />
          <span>Test: Origin Attack</span>
        </button>

        <button 
          onClick={() => runScenario('velocity')}
          disabled={isPlaying}
          className={`flex items-center justify-center space-x-2 px-6 py-4 border-2 border-black font-mono font-bold text-xs uppercase tracking-widest transition-all ${
            activeScenario === 'velocity' 
              ? 'bg-[#EAB308] text-black shadow-[6px_6px_0_0_#000]' 
              : 'bg-[#FDFBF7] text-black hover:bg-black/5 shadow-[4px_4px_0_0_#000] disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Test: Velocity Limit</span>
        </button>
      </div>

      {/* 2. DIAGRAM CONTAINER */}
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
          className="absolute top-0 left-0 w-[12px] h-[12px] bg-black rounded-full z-50 shadow-[0_0_10px_rgba(37,99,235,0.2)]"
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
        <div className="flag-box absolute left-[590px] top-[80px] w-[80px] h-[40px] border-2 border-black bg-[#FDFBF7] text-black text-[10px] font-mono font-bold tracking-widest flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000] transition-colors">
          FLAG
        </div>
        <div className="block-box absolute left-[590px] top-[230px] w-[80px] h-[40px] border-2 border-black bg-[#FDFBF7] text-black text-[10px] font-mono font-bold tracking-widest flex items-center justify-center z-10 shadow-[4px_4px_0_0_#000] transition-colors">
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

      {/* 3. DYNAMIC CAPTION */}
      <div className="mt-12 flex items-center justify-center w-full px-4">
        <p className="text-xs md:text-[14px] font-mono font-bold text-black bg-[#FDFBF7] border-2 border-black px-8 py-4 shadow-[6px_6px_0_0_#000] tracking-tight max-w-3xl text-center min-h-[56px] flex items-center">
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
