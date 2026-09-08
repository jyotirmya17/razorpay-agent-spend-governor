"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface StatCounterProps {
  title: string;
  value: number;
  prefix?: string;
  suffix?: string;
}

export default function StatCounter({ title, value, prefix = "", suffix = "" }: StatCounterProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const numberRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    // Check for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!prefersReducedMotion && numberRef.current) {
      gsap.to(numberRef.current, {
        innerHTML: value,
        duration: 2,
        snap: { innerHTML: 1 },
        ease: "power2.out",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 90%",
          once: true
        }
      });
    } else if (numberRef.current) {
      // Instant display for reduced motion
      numberRef.current.innerHTML = value.toString();
    }
  }, [value]);

  return (
    <div ref={containerRef} className="bg-transparent border-r-2 border-b-2 sm:border-b-0 border-black p-6 flex flex-col items-center justify-center text-center space-y-3 h-full last:border-r-0">
      <div className="text-black text-5xl font-extrabold font-mono tracking-tighter">
        {prefix}<span ref={numberRef}>0</span>{suffix}
      </div>
      <span className="text-xs text-black/60 font-mono font-bold uppercase tracking-widest">{title}</span>
    </div>
  );
}
