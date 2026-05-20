import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const nodeData = [
  { id: "frontend", label: "Frontend Interface", sub: "React · Three.js · WebGL", x: 450, y: 50, level: "L1" },
  { id: "engine", label: "Optimization Engine", sub: "Solver routing · Caching", x: 450, y: 150, level: "L2" },
  { id: "qubo", label: "QUBO Transformation", sub: "Binary encoding · Constraints", x: 450, y: 250, level: "L3" },
  { id: "solvers", label: "Hybrid Solver Layer", sub: "Multi-backend dispatch", x: 450, y: 350, level: "L4" },
  { id: "classical", label: "Classical Solver", sub: "Simulated Annealing", x: 180, y: 470, level: "S1" },
  { id: "qiskit", label: "Qiskit Runtime", sub: "IBM Quantum", x: 450, y: 470, level: "S2" },
  { id: "dwave", label: "D-Wave Hybrid", sub: "Quantum Annealing", x: 720, y: 470, level: "S3" },
  { id: "braket", label: "AWS Braket", sub: "Cloud Infrastructure", x: 450, y: 590, level: "L5" },
  { id: "output", label: "Portfolio Intelligence", sub: "Optimized allocations · Risk", x: 450, y: 690, level: "L6" },
];

const connections = [
  { id: "c1", from: "frontend", to: "engine", type: "straight" },
  { id: "c2", from: "engine", to: "qubo", type: "straight" },
  { id: "c3", from: "qubo", to: "solvers", type: "straight" },
  { id: "c4", from: "solvers", to: "classical", type: "curve" },
  { id: "c5", from: "solvers", to: "qiskit", type: "straight" },
  { id: "c6", from: "solvers", to: "dwave", type: "curve" },
  { id: "c7", from: "classical", to: "braket", type: "curve" },
  { id: "c8", from: "qiskit", to: "braket", type: "straight" },
  { id: "c9", from: "dwave", to: "braket", type: "curve" },
  { id: "c10", from: "braket", to: "output", type: "straight" },
];

export function ArchitectureDiagram() {
  const containerRef = useRef<HTMLDivElement>(null);
  const pinRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  // Refs for animation targets
  const nodeRefs = useRef<Record<string, SVGGElement | null>>({});
  const pathRefs = useRef<Record<string, SVGPathElement | null>>({});

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    if (isMobile || !containerRef.current || !pinRef.current) {
      // Un-hide all if mobile
      Object.values(nodeRefs.current).forEach((el) => {
        if (el) {
          gsap.set(el, { opacity: 1, scale: 1 });
        }
      });
      Object.values(pathRefs.current).forEach((el) => {
        if (el) {
          gsap.set(el, { strokeDashoffset: 0 });
        }
      });
      return;
    }

    // Setup initial states
    Object.values(nodeRefs.current).forEach((el) => {
      if (el) gsap.set(el, { opacity: 0, scale: 0.9, transformOrigin: "center center" });
    });

    Object.values(pathRefs.current).forEach((el) => {
      if (el) {
        const len = el.getTotalLength();
        gsap.set(el, { strokeDasharray: len, strokeDashoffset: len });
      }
    });

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: containerRef.current,
        start: "top top",
        end: "+=300%",
        pin: pinRef.current,
        scrub: 1,
      },
    });

    const revealNode = (id: string) => {
      const el = nodeRefs.current[id];
      if (el) tl.to(el, { opacity: 1, scale: 1, duration: 0.4, ease: "power2.out" }, ">-0.1");
    };

    const drawLine = (id: string) => {
      const el = pathRefs.current[id];
      if (el) tl.to(el, { strokeDashoffset: 0, duration: 0.6, ease: "power1.inOut" }, ">-0.2");
    };

    // Sequence
    revealNode("frontend");
    drawLine("c1");
    revealNode("engine");
    drawLine("c2");
    revealNode("qubo");
    drawLine("c3");
    revealNode("solvers");

    // Fan out to solvers
    const tFanStart = tl.duration();
    ["c4", "c5", "c6"].forEach((c) => {
      const el = pathRefs.current[c];
      if (el) tl.to(el, { strokeDashoffset: 0, duration: 0.6, ease: "power1.inOut" }, tFanStart);
    });

    const tSolversStart = tFanStart + 0.4;
    ["classical", "qiskit", "dwave"].forEach((s) => {
      const el = nodeRefs.current[s];
      if (el) tl.to(el, { opacity: 1, scale: 1, duration: 0.4, ease: "power2.out" }, tSolversStart);
    });

    // Merge to Braket
    const tMergeStart = tl.duration();
    ["c7", "c8", "c9"].forEach((c) => {
      const el = pathRefs.current[c];
      if (el) tl.to(el, { strokeDashoffset: 0, duration: 0.6, ease: "power1.inOut" }, tMergeStart);
    });
    
    revealNode("braket");
    drawLine("c10");
    revealNode("output");

    // Final pulse
    tl.to(Object.values(nodeRefs.current), {
      scale: 1.02,
      duration: 0.3,
      stagger: 0.02,
      ease: "power2.out",
    }).to(Object.values(nodeRefs.current), {
      scale: 1,
      duration: 0.3,
      stagger: 0.02,
      ease: "power2.in",
    });

    return () => {
      tl.kill();
    };
  }, [isMobile]);

  // SVG Path generator
  const getPath = (c: typeof connections[0]) => {
    const n1 = nodeData.find((n) => n.id === c.from)!;
    const n2 = nodeData.find((n) => n.id === c.to)!;
    const x1 = n1.x;
    const y1 = n1.y + 30; // Bottom of node
    const x2 = n2.x;
    const y2 = n2.y - 30; // Top of node

    if (c.type === "straight") {
      return `M ${x1},${y1} L ${x2},${y2}`;
    } else {
      const midY = y1 + (y2 - y1) / 2;
      return `M ${x1},${y1} C ${x1},${midY} ${x2},${midY} ${x2},${y2}`;
    }
  };

  return (
    <section id="architecture" className="relative py-32 overflow-hidden bg-background">
      <div className="absolute inset-0 bg-aurora opacity-30 pointer-events-none" />
      
      <div className="relative mx-auto max-w-7xl px-6 mb-16 z-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-primary/90 shadow-[0_0_20px_-5px_oklch(0.65_0.27_295/30%)]">
          <span className="h-1 w-1 rounded-full bg-primary animate-pulse" />
          Built On A Hybrid Stack
        </div>
        <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.02em]">
          <span className="text-gradient-quantum">Quantum-classical</span> architecture.
        </h2>
      </div>

      <div ref={containerRef}>
        <div ref={pinRef} className={isMobile ? "" : "min-h-screen flex items-center justify-center pt-10"}>
          <div className="mx-auto max-w-[1000px] w-full px-4">
            <div className="glass-card rounded-3xl p-4 md:p-8 relative shadow-[0_30px_80px_-20px_oklch(0.09_0.02_280/80%)]">
              <svg viewBox="0 0 900 750" className="w-full h-auto drop-shadow-2xl">
                <defs>
                  <linearGradient id="archNodeGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="oklch(1 0 0 / 6%)" />
                    <stop offset="100%" stopColor="oklch(1 0 0 / 2%)" />
                  </linearGradient>
                  <linearGradient id="archOutputGrad" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.65 0.27 295 / 25%)" />
                    <stop offset="100%" stopColor="oklch(0.7 0.22 250 / 25%)" />
                  </linearGradient>
                  <pattern id="archGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="oklch(1 0 0 / 3%)" strokeWidth="0.5" />
                  </pattern>
                  <marker id="archArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="oklch(0.65 0.27 295 / 60%)" />
                  </marker>
                  <filter id="nodeGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="8" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                {/* Grid */}
                <rect width="900" height="750" fill="url(#archGrid)" rx="16" />

                {/* Figure Labels */}
                <text x="20" y="30" fontSize="10" fontFamily="JetBrains Mono, monospace" fill="oklch(0.6 0.05 280)">
                  SYSTEM ARCHITECTURE
                </text>
                <text x="880" y="730" textAnchor="end" fontSize="10" fontFamily="JetBrains Mono, monospace" fill="oklch(0.6 0.05 280)">
                  FIG.02 — QURVE CORE
                </text>

                {/* Connections */}
                <g>
                  {connections.map((c) => {
                    const isHovered = hoveredNode === c.from || hoveredNode === c.to;
                    return (
                      <path
                        key={c.id}
                        ref={(el) => { pathRefs.current[c.id] = el; }}
                        d={getPath(c)}
                        fill="none"
                        stroke={isHovered ? "oklch(0.7 0.22 250)" : "oklch(0.65 0.27 295 / 40%)"}
                        strokeWidth={isHovered ? "2.5" : "1.5"}
                        markerEnd="url(#archArrow)"
                        className="transition-colors duration-300"
                        style={{ willChange: "stroke-dashoffset" }}
                      />
                    );
                  })}
                </g>

                {/* Nodes */}
                <g>
                  {nodeData.map((node) => {
                    const isHovered = hoveredNode === node.id;
                    const isOutput = node.id === "output";
                    return (
                      <g
                        key={node.id}
                        ref={(el) => { nodeRefs.current[node.id] = el; }}
                        onMouseEnter={() => setHoveredNode(node.id)}
                        onMouseLeave={() => setHoveredNode(null)}
                        className="cursor-pointer"
                        style={{ transformOrigin: `${node.x}px ${node.y}px`, willChange: "transform, opacity" }}
                      >
                        <rect
                          x={node.x - 100}
                          y={node.y - 30}
                          width="200"
                          height="60"
                          rx="12"
                          fill={isOutput ? "url(#archOutputGrad)" : "url(#archNodeGrad)"}
                          stroke={isHovered ? "oklch(0.75 0.27 295)" : isOutput ? "oklch(0.65 0.27 295 / 80%)" : "oklch(0.65 0.27 295 / 30%)"}
                          strokeWidth={isHovered || isOutput ? "1.5" : "1"}
                          filter={isHovered || isOutput ? "url(#nodeGlow)" : "none"}
                          className="transition-all duration-300"
                          style={{
                            transform: isHovered ? "scale(1.05)" : "scale(1)",
                            transformOrigin: "center center",
                          }}
                        />
                        <text
                          x={node.x}
                          y={node.y - 2}
                          fontSize="13"
                          fontFamily="Space Grotesk, sans-serif"
                          fill="oklch(0.95 0.02 280)"
                          textAnchor="middle"
                          fontWeight="600"
                          style={{ pointerEvents: "none" }}
                        >
                          {node.label}
                        </text>
                        <text
                          x={node.x}
                          y={node.y + 14}
                          fontSize="10"
                          fontFamily="JetBrains Mono, monospace"
                          fill={isHovered ? "oklch(0.8 0.1 260)" : "oklch(0.6 0.05 280)"}
                          textAnchor="middle"
                          className="transition-colors duration-300"
                          style={{ pointerEvents: "none" }}
                        >
                          {node.sub}
                        </text>
                        <text
                          x={node.x + 88}
                          y={node.y - 18}
                          fontSize="9"
                          fontFamily="JetBrains Mono, monospace"
                          fill="oklch(0.65 0.27 295 / 60%)"
                          textAnchor="end"
                          style={{ pointerEvents: "none" }}
                        >
                          {node.level}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
