import { useEffect, useRef, useState, useCallback } from "react";
import { gsap, ScrollTrigger } from "@/lib/gsap";

/* ─── Step data ─────────────────────────────────────────────── */

interface Step {
  n: string;
  title: string;
  desc: string;
  code: string;
}

const steps: Step[] = [
  {
    n: "01",
    title: "User Constraints",
    desc: "Portfolio preferences and financial constraints enter the system through a structured input contract.",
    code: 'constraints = { budget: 1e6, risk_tolerance: 0.15, sectors: ["tech", "healthcare"] }',
  },
  {
    n: "02",
    title: "QUBO Transformation",
    desc: "Optimization variables are encoded into scalable QUBO formulations with binary precision.",
    code: "Q = encode_qubo(constraints, covariance_matrix, expected_returns)",
  },
  {
    n: "03",
    title: "Hybrid Solver Selection",
    desc: "A computational layer dynamically selects the optimal hybrid execution pathway.",
    code: "solver = select_optimal_solver(Q.density, Q.size, backends)",
  },
  {
    n: "04",
    title: "Quantum-Classical Execution",
    desc: "Hybrid solvers process and optimize portfolio configurations across compute backends.",
    code: "result = hybrid_solve(Q, solver, iterations=1000, eps=1e-6)",
  },
  {
    n: "05",
    title: "Intelligent Output",
    desc: "Advanced insights and optimized allocations are visualized interactively in real-time.",
    code: "portfolio = decode_solution(result, tickers, weights, risk_metrics)",
  },
];

/* ─── SVG timeline geometry ─────────────────────────────────── */

const SVG_W = 40;
const SVG_H = 500;
const NODE_CX = 20;
const NODE_R = 8;
const LINE_Y1 = 30;
const LINE_Y2 = 470;
const TOTAL_LINE_LENGTH = LINE_Y2 - LINE_Y1; // 440
const NODE_YS = [30, 140, 250, 360, 470] as const;

/* ─── Desktop pinned scroll story ───────────────────────────── */

function DesktopTimeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const pinRef = useRef<HTMLDivElement>(null);
  const lineRef = useRef<SVGLineElement>(null);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    const pin = pinRef.current;
    const line = lineRef.current;
    if (!container || !pin || !line) return;

    // Initialize SVG line dasharray for progressive draw
    gsap.set(line, {
      attr: {
        "stroke-dasharray": TOTAL_LINE_LENGTH,
        "stroke-dashoffset": TOTAL_LINE_LENGTH,
      },
    });

    const trigger = ScrollTrigger.create({
      trigger: container,
      start: "top top",
      end: "+=400%",
      pin: pin,
      pinSpacing: true,
      scrub: 1,
      onUpdate: (self) => {
        const step = Math.min(4, Math.floor(self.progress * 5));
        setActiveStep(step);

        // Draw SVG line progressively with scroll
        if (lineRef.current) {
          lineRef.current.style.strokeDashoffset = String(
            TOTAL_LINE_LENGTH * (1 - self.progress)
          );
        }
      },
    });

    return () => {
      trigger.kill();
    };
  }, []);

  return (
    <div ref={containerRef}>
      <div ref={pinRef} className="min-h-screen flex items-center">
        <div className="mx-auto max-w-7xl px-6 w-full">
          <div className="grid lg:grid-cols-[280px_1fr] gap-12 items-start">
            {/* ── Left: SVG Timeline Column ── */}
            <div className="flex justify-center">
              <svg
                viewBox={`0 0 ${SVG_W} ${SVG_H}`}
                width={SVG_W}
                height={SVG_H}
                className="flex-shrink-0"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient
                    id="tl-line-grad"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="oklch(0.65 0.27 295)" />
                    <stop offset="100%" stopColor="oklch(0.7 0.22 250)" />
                  </linearGradient>
                  <linearGradient
                    id="tl-node-grad"
                    x1="0"
                    y1="0"
                    x2="1"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="oklch(0.65 0.27 295)" />
                    <stop offset="100%" stopColor="oklch(0.78 0.18 200)" />
                  </linearGradient>
                </defs>

                {/* Background track line */}
                <line
                  x1={NODE_CX}
                  y1={LINE_Y1}
                  x2={NODE_CX}
                  y2={LINE_Y2}
                  stroke="oklch(0.65 0.27 295 / 10%)"
                  strokeWidth={2}
                />

                {/* Animated progress line */}
                <line
                  ref={lineRef}
                  x1={NODE_CX}
                  y1={LINE_Y1}
                  x2={NODE_CX}
                  y2={LINE_Y2}
                  stroke="url(#tl-line-grad)"
                  strokeWidth={2}
                  strokeLinecap="round"
                />

                {/* Step circles + step number labels */}
                {steps.map((step, i) => {
                  const cy = NODE_YS[i];
                  const isActive = i === activeStep;
                  const isPast = i < activeStep;

                  return (
                    <g key={step.n}>
                      {/* Outer glow ring for active node */}
                      {isActive && (
                        <circle
                          cx={NODE_CX}
                          cy={cy}
                          r={14}
                          fill="none"
                          stroke="oklch(0.65 0.27 295 / 25%)"
                          strokeWidth={1}
                          style={{ transition: "opacity 0.4s ease" }}
                        />
                      )}

                      {/* Main node circle */}
                      <circle
                        cx={NODE_CX}
                        cy={cy}
                        r={NODE_R}
                        fill={
                          isActive
                            ? "url(#tl-node-grad)"
                            : isPast
                              ? "oklch(0.65 0.27 295 / 60%)"
                              : "none"
                        }
                        stroke={
                          isActive
                            ? "oklch(0.65 0.27 295)"
                            : isPast
                              ? "oklch(0.65 0.27 295 / 60%)"
                              : "oklch(0.65 0.27 295 / 30%)"
                        }
                        strokeWidth={isActive || isPast ? 0 : 1.5}
                        style={{
                          transform: isActive ? "scale(1.3)" : "scale(1)",
                          transformOrigin: `${NODE_CX}px ${cy}px`,
                          transition:
                            "transform 0.4s ease, fill 0.4s ease, stroke 0.4s ease",
                          filter: isActive
                            ? "drop-shadow(0 0 8px oklch(0.65 0.27 295 / 60%))"
                            : "none",
                        }}
                      />

                      {/* Step number text */}
                      <text
                        x={50}
                        y={cy + 4}
                        fontFamily="var(--font-mono)"
                        fontSize={11}
                        fill={
                          isActive
                            ? "oklch(0.85 0.18 280)"
                            : isPast
                              ? "oklch(0.65 0.27 295 / 60%)"
                              : "oklch(0.65 0.04 270)"
                        }
                        style={{ transition: "fill 0.4s ease" }}
                      >
                        {step.n}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* ── Right: Content Panel ── */}
            <div className="relative" style={{ minHeight: 420 }}>
              {steps.map((step, i) => {
                const isActive = i === activeStep;

                return (
                  <div
                    key={step.n}
                    className="absolute inset-0"
                    style={{
                      opacity: isActive ? 1 : 0,
                      transform: isActive
                        ? "translateY(0)"
                        : "translateY(20px)",
                      pointerEvents: isActive ? "auto" : "none",
                      transition:
                        "opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1), transform 0.45s cubic-bezier(0.22, 1, 0.36, 1)",
                      willChange: "opacity, transform",
                    }}
                  >
                    {/* Step number watermark */}
                    <div
                      className="font-mono text-8xl font-bold select-none pointer-events-none"
                      style={{ color: "oklch(0.65 0.27 295 / 12%)" }}
                      aria-hidden="true"
                    >
                      {step.n}
                    </div>

                    {/* Title */}
                    <h3 className="font-display text-3xl lg:text-4xl font-medium tracking-tight text-foreground mt-2">
                      {step.title}
                    </h3>

                    {/* Description */}
                    <p className="text-lg text-muted-foreground leading-relaxed max-w-lg mt-4">
                      {step.desc}
                    </p>

                    {/* Code block */}
                    <div className="glass-card border-glow rounded-xl mt-8 max-w-lg overflow-hidden transform-gpu will-change-transform" style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}>
                      {/* Window chrome dots */}
                      <div className="flex items-center gap-2 px-4 pt-4 pb-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ background: "oklch(0.6 0.2 25)" }}
                        />
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ background: "oklch(0.7 0.2 85)" }}
                        />
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ background: "oklch(0.6 0.2 145)" }}
                        />
                        <span className="ml-auto font-mono text-[10px] text-muted-foreground/50">
                          qurve_pipeline.py
                        </span>
                      </div>
                      <code
                        className="font-mono text-sm block px-4 pb-4 pt-1 leading-relaxed"
                        style={{
                          color: "oklch(0.78 0.18 200)",
                          wordBreak: "break-all",
                        }}
                      >
                        {step.code}
                      </code>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Mobile cards (no pinning) ─────────────────────────────── */

function MobileTimeline() {
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  const setCardRef = useCallback(
    (idx: number) => (el: HTMLDivElement | null) => {
      cardRefs.current[idx] = el;
    },
    []
  );

  useEffect(() => {
    const triggers: ScrollTrigger[] = [];

    cardRefs.current.forEach((card) => {
      if (!card) return;

      gsap.set(card, { opacity: 0, y: 40 });

      const st = ScrollTrigger.create({
        trigger: card,
        start: "top 85%",
        onEnter: () => {
          gsap.to(card, {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: "power3.out",
          });
        },
        once: true,
      });

      triggers.push(st);
    });

    return () => {
      triggers.forEach((st) => st.kill());
    };
  }, []);

  return (
    <div className="flex flex-col gap-6 px-4">
      {steps.map((step, i) => (
        <div
          key={step.n}
          ref={setCardRef(i)}
          className="glass-card border-glow rounded-2xl p-6 will-change-transform transform-gpu"
          style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}
        >
          {/* Header row */}
          <div className="flex items-center gap-3 mb-4">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0"
              style={{
                background:
                  "linear-gradient(135deg, oklch(0.65 0.27 295), oklch(0.7 0.22 250))",
              }}
            >
              <span className="font-mono text-sm font-bold text-white">
                {step.n}
              </span>
            </div>
            <h3 className="font-display text-xl font-medium text-foreground">
              {step.title}
            </h3>
          </div>

          {/* Description */}
          <p className="text-muted-foreground text-base leading-relaxed mb-5">
            {step.desc}
          </p>

          {/* Code snippet */}
          <div
            className="rounded-lg p-3"
            style={{
              background: "oklch(0.11 0.025 280)",
              border: "1px solid oklch(1 0 0 / 6%)",
            }}
          >
            <code
              className="font-mono text-xs block"
              style={{
                color: "oklch(0.78 0.18 200)",
                wordBreak: "break-all",
              }}
            >
              {step.code}
            </code>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Main export ───────────────────────────────────────────── */

export function ScrollStory() {
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) =>
      setIsDesktop(e.matches);
    handler(mql);
    mql.addEventListener("change", handler as (e: MediaQueryListEvent) => void);
    return () =>
      mql.removeEventListener(
        "change",
        handler as (e: MediaQueryListEvent) => void
      );
  }, []);

  return (
    <section className="relative noise" id="scroll-story">
      {/* Section header — sits OUTSIDE the pinned area */}
      <div className="mx-auto max-w-7xl px-6 mb-16 pt-32">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-primary/90">
          <span className="h-1 w-1 rounded-full bg-primary animate-pulse" />
          From Constraints to Intelligence
        </div>
        <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.02em]">
          From financial constraints to{" "}
          <span className="text-gradient-quantum">quantum intelligence</span>.
        </h2>
      </div>

      {/* Timeline body */}
      <div className="relative">
        {/* Subtle aurora glow behind the timeline */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 40% at 30% 50%, oklch(0.65 0.27 295 / 8%) 0%, transparent 70%), radial-gradient(ellipse 50% 50% at 80% 60%, oklch(0.7 0.22 250 / 6%) 0%, transparent 70%)",
          }}
        />

        <div style={{ height: isDesktop ? undefined : "auto" }}>
          {isDesktop ? <DesktopTimeline /> : <MobileTimeline />}
        </div>
      </div>
    </section>
  );
}
