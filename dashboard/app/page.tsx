"use client";

import Link from "next/link";
import { ArrowRight, PlayCircle } from "lucide-react";
import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import SplitType from "split-type";
import ArchitectureDiagram from "@/components/landing/ArchitectureDiagram";
import StatCounter from "@/components/landing/StatCounter";

gsap.registerPlugin(useGSAP, ScrollTrigger);

const LOOM_EMBED_URL: string = "https://www.loom.com/embed/500a29da79074e878ec80e008de7727e";

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // Check for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (!prefersReducedMotion) {
      // 1. Hero Load Animation
      const tl = gsap.timeline();
      
      tl.from(".hero-badge", {
        y: 20, opacity: 0, duration: 0.6, stagger: 0.1, ease: "power2.out"
      })
      .from(".hero-headline", {
        y: 20, opacity: 0, duration: 0.6, ease: "power2.out"
      }, "-=0.3")
      .from(".hero-subtext", {
        y: 20, opacity: 0, duration: 0.6, ease: "power2.out"
      }, "-=0.3")
      .from(".hero-btn", {
        y: 20, opacity: 0, duration: 0.6, stagger: 0.1, ease: "power2.out"
      }, "-=0.3");

      // 2. Scroll Reveals
      const revealElements = gsap.utils.toArray<HTMLElement>('.gsap-reveal');
      
      revealElements.forEach((el) => {
        gsap.from(el, {
          y: 40,
          opacity: 0,
          duration: 0.8,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 85%", 
            once: true
          }
        });
      });

      // 3. Problem Section Scrub Reveal (Line by Line)
      const problemText = document.querySelector('.problem-text');
      let split: any = null;
      
      if (problemText) {
        // Automatically splits the paragraph into visual DOM lines
        split = new SplitType(problemText as HTMLElement, { types: 'lines', lineClass: 'problem-split-line' });
        
        if (split.lines && split.lines.length > 0) {
          gsap.set(split.lines, { 
            opacity: 0.15, 
            color: "#000000",
            WebkitTextStrokeWidth: "0px",
            WebkitTextStrokeColor: "#000000"
          });
          gsap.to(split.lines, {
            opacity: 1,
            WebkitTextStrokeWidth: "2px", // Extremely smooth, fat bolding without layout shift
            stagger: 0.1,
            scrollTrigger: {
              trigger: ".problem-section",
              start: "top 70%",
              end: "bottom 70%",
              scrub: 1.5,
            }
          });
        }
      }
      
      // Button hover effects
      const primaryBtn = document.querySelector('.primary-btn');
      if (primaryBtn) {
        const arrow = primaryBtn.querySelector('.arrow-icon');
        primaryBtn.addEventListener('mouseenter', () => {
          gsap.to(primaryBtn, { y: -2, boxShadow: "0 8px 30px rgba(0,0,0,0.3)", duration: 0.2, ease: "power1.out" });
          gsap.to(arrow, { x: 4, duration: 0.2, ease: "power1.out" });
        });
        primaryBtn.addEventListener('mouseleave', () => {
          gsap.to(primaryBtn, { y: 0, boxShadow: "0 0px 0px rgba(0,0,0,0)", duration: 0.2, ease: "power1.in" });
          gsap.to(arrow, { x: 0, duration: 0.2, ease: "power1.in" });
        });
      }

      return () => {
        if (split) {
          split.revert();
        }
      };
    }
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="min-h-screen bg-[#FDFBF7] text-[#000000] font-sans overflow-x-hidden selection:bg-[#000000] selection:text-[#FDFBF7]">
      
      {/* 1. HERO */}
      <section className="relative px-6 pt-24 pb-16 min-h-[80vh] flex flex-col justify-center border-b border-black/10">
        
        <div className="max-w-6xl mx-auto w-full relative z-10 flex flex-col items-start space-y-8">
          <div className="flex flex-wrap gap-3">
            <Badge className="hero-badge" text="DETERMINISTIC POLICY" />
            <Badge className="hero-badge" text="BEHAVIORAL ANOMALY DETECTION" />
            <Badge className="hero-badge" text="INSTRUCTION PROVENANCE" />
            <Badge className="hero-badge" text="TAMPER-EVIDENT AUDIT" />
          </div>
          
          <h1 className="hero-headline font-general text-6xl md:text-[clamp(3.5rem,8vw,7rem)] font-extrabold tracking-tighter text-black leading-[0.95] max-w-5xl">
            An AI agent can be fully authorized to pay and still be hijacked.
          </h1>
          
          <p className="hero-subtext text-xl md:text-[1.25rem] text-black/80 max-w-3xl leading-[1.6] font-medium">
            Because traditional authorization checks <em>what</em> was decided, not <em>why</em>. Agent Spend Governor is the missing defense layer between autonomous agents and RazorpayX.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center gap-6 pt-4">
            <Link
              href="/dashboard"
              className="primary-btn hero-btn px-10 py-5 bg-black text-[#FDFBF7] font-bold transition-colors flex items-center space-x-3 text-sm tracking-widest uppercase rounded-sm"
            >
              <span>View Live Dashboard</span>
              <ArrowRight className="arrow-icon w-5 h-5" />
            </Link>
            <a
              href="https://github.com/jyotirmya17/razorpay-agent-spend-governor"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-btn px-10 py-5 bg-transparent hover:bg-black/5 border-2 border-black text-black font-bold transition-colors text-sm tracking-widest uppercase rounded-sm"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* 2. THE PROBLEM */}
      <section className="problem-section px-6 py-40 border-b border-black/10">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-sm font-mono text-black uppercase tracking-widest mb-12 font-bold opacity-60">The Problem</h2>
          <p className="problem-text text-3xl md:text-5xl lg:text-[3.25rem] text-black text-justify leading-[1.2] font-medium font-general tracking-tight">
            Imagine an authorized AI agent reading an untrusted invoice. An invisible prompt injection redirects the payment instruction to an attacker's account. Every field looks structurally normal. Traditional controls—maker-checker flows, budgets, and card limits—will miss this attack because none of them verify the origin of the instruction payload.
          </p>
        </div>
      </section>

      {/* 3. ARCHITECTURE */}
      <section className="px-6 py-32 border-b border-black/10">
        <div className="max-w-5xl mx-auto gsap-reveal">
          <h2 className="text-sm font-mono text-black uppercase tracking-widest mb-16 text-center font-bold opacity-60">System Architecture</h2>
          <ArchitectureDiagram />
        </div>
      </section>

      {/* 3.5 WHERE TO LOOK FIRST */}
      <section className="px-6 py-32 border-b border-black/10 bg-[#FDFBF7]">
        <div className="max-w-5xl mx-auto gsap-reveal">
          <h2 className="text-sm font-mono text-black uppercase tracking-widest mb-16 font-bold opacity-60 text-center">Where to Look First</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            
            <div className="border-t-4 border-amber-500 pt-6">
              <span className="text-4xl font-extrabold font-general text-amber-500/20 block mb-4">01</span>
              <h3 className="text-lg font-bold font-general text-black mb-3">Governance Scenarios</h3>
              <p className="text-sm font-mono text-black/70 leading-relaxed">
                Use the sidebar to navigate to Governance Scenarios — watch a payout get Allowed, Flagged, or Blocked live.
              </p>
            </div>
            
            <div className="border-t-4 border-amber-500 pt-6">
              <span className="text-4xl font-extrabold font-general text-amber-500/20 block mb-4">02</span>
              <h3 className="text-lg font-bold font-general text-black mb-3">Audit Trail Page</h3>
              <p className="text-sm font-mono text-black/70 leading-relaxed">
                Check the tamper-evident decision log to see immutable, cryptographically-hashed decision logs.
              </p>
            </div>
            
            <div className="border-t-4 border-amber-500 pt-6">
              <span className="text-4xl font-extrabold font-general text-amber-500/20 block mb-4">03</span>
              <h3 className="text-lg font-bold font-general text-black mb-3">Provenance / Injection</h3>
              <p className="text-sm font-mono text-black/70 leading-relaxed">
                The provenance/injection scenario is the core differentiator — look for it specifically.
              </p>
            </div>

          </div>
          <div className="mt-16 text-center">
            <a href="https://github.com/jyotirmya17/razorpay-agent-spend-governor#where-to-look-first" target="_blank" rel="noopener noreferrer" className="text-sm font-mono font-bold text-amber-600 hover:text-amber-700 hover:bg-amber-50 border-2 border-amber-500/30 px-6 py-3 transition-colors inline-flex items-center space-x-3 rounded-sm uppercase tracking-widest">
              <span>Detailed guide</span>
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* 4. THE VIDEO */}
      <section id="demo-video" className="px-6 py-32 border-b border-black/10">
        <div className="max-w-5xl mx-auto gsap-reveal">
          <h2 className="text-sm font-mono text-black uppercase tracking-widest mb-10 text-center font-bold opacity-60">Demo Walkthrough</h2>
          <div className="aspect-video w-full bg-black border border-black/20 overflow-hidden relative flex items-center justify-center group shadow-2xl rounded-sm">
            {LOOM_EMBED_URL !== "REPLACE_ME" ? (
              <iframe 
                src={LOOM_EMBED_URL} 
                frameBorder="0" 
                allowFullScreen 
                className="absolute inset-0 w-full h-full"
              ></iframe>
            ) : (
              <div className="text-white/40 flex flex-col items-center space-y-6">
                <PlayCircle className="w-20 h-20 opacity-30 group-hover:opacity-100 group-hover:text-[#FDFBF7] transition-all cursor-pointer" />
                <span className="font-mono text-xs uppercase tracking-widest text-white/50">Loom Embed Placeholder</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 5. THE HONEST FINDING */}
      <section className="px-6 py-32 border-b border-black/10">
        <div className="max-w-4xl mx-auto text-center gsap-reveal">
          <h2 className="text-sm font-mono text-black uppercase tracking-widest mb-10 font-bold opacity-60">The Honest Finding: Rules vs ML</h2>
          <div className="p-10 border-2 border-black shadow-[8px_8px_0_0_#000] bg-[#FDFBF7] rounded-sm relative">
            <p className="text-xl md:text-3xl text-black leading-relaxed text-left font-semibold font-general tracking-tight relative z-10">
              A simple deterministic rules baseline currently beats the ML model on aggregate cost. Evaluating over historical distributions, rigid caps stop simple over-spend more cheaply. The true value of the ML layer is not in broad statistical coverage, but in acting as a safety net against <strong className="font-extrabold underline decoration-4 underline-offset-4">adversarial, multi-signal attacks</strong>—like a hijacked agent splitting a large illicit payload across multiple small, varied transactions that individually bypass static rule caps.
            </p>
          </div>
        </div>
      </section>

      {/* 6. STAT STRIP */}
      <section className="px-6 py-32 border-b border-black/10">
        <div className="max-w-6xl mx-auto gsap-reveal">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-0 border-2 border-black rounded-sm overflow-hidden shadow-[8px_8px_0_0_#000]">
            <StatCounter title="Tests Passing" value={125} suffix="/125" />
            <StatCounter title="Audit Chain" value={256} prefix="SHA-" />
            <StatCounter title="Database Lock" value={1} prefix="ROW LEVEL " suffix="X" />
            <StatCounter title="ML Evaluation" value={100} suffix="% HELD OUT" />
          </div>
        </div>
      </section>

      {/* 7. FOOTER */}
      <footer className="px-6 py-16 text-center space-y-8 gsap-reveal">
        <div className="flex justify-center space-x-10 text-xs font-mono uppercase tracking-widest font-bold">
          <Link href="/dashboard" className="text-black/60 hover:text-black transition-colors">Dashboard Console</Link>
          <a href="https://github.com/jyotirmya17/razorpay-agent-spend-governor" target="_blank" rel="noopener noreferrer" className="text-black/60 hover:text-black transition-colors">GitHub Repository</a>
        </div>
        <p className="text-[#888888]">
          &copy; {new Date().getFullYear()} Spend Governor. All rights reserved.
        </p>
      </footer>
    </div>
  );
}

function Badge({ text, className = "" }: { text: string, className?: string }) {
  return (
    <span className={`px-4 py-2 border-2 border-black bg-[#FDFBF7] text-[11px] font-mono font-bold tracking-widest text-black uppercase rounded-sm ${className}`}>
      {text}
    </span>
  );
}
