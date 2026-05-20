import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import React, { useRef } from "react";
import { ArrowRight, Atom, Brain, BarChart3, Cloud, Zap, Sparkles, ArrowUpRight, Cpu, Network, Layers, Github } from "lucide-react";
import { QuantumScene } from "../components/QuantumScene";
import { Nav } from "../components/Nav";
import { ScrollStory } from "../components/ScrollStory";
import { ArchitectureDiagram } from "../components/ArchitectureDiagram";
import { TiltCard } from "../components/TiltCard";
import { MagneticButton } from "../components/MagneticButton";

const ease = [0.22, 1, 0.36, 1] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.9, ease } },
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-primary/90">
      <span className="h-1 w-1 rounded-full bg-primary animate-pulse" />
      {children}
    </div>
  );
}

/* ============== HERO ============== */
function Hero() {
  return (
    <section className="relative w-full overflow-hidden min-h-screen pt-32">
      {/* Aurora background */}
      <div className="absolute inset-0 bg-aurora pointer-events-none" />
      <div className="absolute inset-0 grid-bg pointer-events-none" />

      {/* 3D scene */}
      <div className="absolute inset-0 w-full h-full z-0 pointer-events-none opacity-90">
        <QuantumScene />
      </div>

      {/* Glow orbs */}
      <div className="absolute top-1/4 -left-32 h-[500px] w-[500px] rounded-full bg-primary/20 blur-[120px] animate-pulse-glow" />
      <div className="absolute bottom-1/4 -right-32 h-[500px] w-[500px] rounded-full bg-accent/20 blur-[120px] animate-pulse-glow" style={{ animationDelay: "2s" }} />

      <div className="relative z-10 mx-auto max-w-7xl px-6 pt-20 pb-32 transform-gpu will-change-transform">
        <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.12 } } }} className="max-w-4xl">
          <motion.div variants={fadeUp}>
            <SectionLabel>Quantum-Inspired Portfolio Optimization</SectionLabel>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            className="font-display mt-8 text-[clamp(2.5rem,7vw,5.5rem)] font-medium leading-[1.02] tracking-[-0.03em]"
          >
            Engineering the
            <br />
            future of{" "}
            <span className="text-gradient-quantum">quantum portfolio</span>
            <br />
            intelligence.
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="mt-8 max-w-xl text-base md:text-lg leading-relaxed text-muted-foreground"
          >
            Hybrid quantum-classical optimization platform leveraging QUBO modeling, advanced
            computational heuristics, and next-generation architectures for intelligent
            financial decision-making.
          </motion.p>

          <motion.div variants={fadeUp} className="mt-10 flex flex-wrap items-center gap-4">
            <MagneticButton>
              <Link
                to="/login"
                className="group relative inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary via-primary to-accent px-6 py-3.5 text-sm font-medium text-primary-foreground shadow-[0_0_40px_-8px_oklch(0.65_0.27_295/70%)] transition-all hover:shadow-[0_0_60px_-8px_oklch(0.65_0.27_295/90%)] hover:scale-[1.02]"
              >
                Launch Platform
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </MagneticButton>
            <MagneticButton>
              <a
                href="#architecture"
                className="group inline-flex items-center gap-2 rounded-full border border-border bg-card/40 backdrop-blur px-6 py-3.5 text-sm font-medium text-foreground hover:bg-card/70 transition-colors"
              >
                View Architecture
                <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
            </MagneticButton>
          </motion.div>

          {/* Stats */}
          <motion.div variants={fadeUp} className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-px bg-border/40 rounded-2xl overflow-hidden border border-border/40 max-w-3xl transform-gpu will-change-transform">
            {[
              { v: "10x+", l: "Optimization Speed" },
              { v: "99.8%", l: "Computational Accuracy" },
              { v: "1000+", l: "Assets Analyzed" },
              { v: "24/7", l: "System Availability" },
            ].map((s) => (
              <div key={s.l} className="bg-background/60 backdrop-blur-sm p-5">
                <div className="font-display text-2xl md:text-3xl font-medium text-gradient-quantum">{s.v}</div>
                <div className="mt-1 text-xs text-muted-foreground">{s.l}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

/* ============== TECH MARQUEE ============== */
function TechStrip() {
  const techs = ["D-Wave Ocean SDK", "IBM Qiskit", "AWS Braket", "Python", "FastAPI", "React", "Three.js", "Pandas", "NumPy", "PyTorch"];
  const row = [...techs, ...techs];
  return (
    <section className="relative py-20 border-y border-border/40 bg-card/20">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-center text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground mb-10">
          Built with advanced computational technologies
        </p>
      </div>
      <div className="relative overflow-hidden mask-fade">
        <div className="flex gap-4 animate-marquee w-max">
          {row.map((t, i) => (
            <div key={i} className="glass-card flex items-center gap-3 rounded-2xl px-6 py-4 min-w-[220px]">
              <div className="h-2 w-2 rounded-full bg-gradient-to-br from-primary to-accent shadow-[0_0_10px_oklch(0.65_0.27_295)]" />
              <span className="font-display text-sm font-medium whitespace-nowrap">{t}</span>
            </div>
          ))}
        </div>
      </div>
      <style>{`.mask-fade { mask-image: linear-gradient(90deg, transparent, black 10%, black 90%, transparent); }`}</style>
    </section>
  );
}

/* ============== FEATURES ============== */
function Features() {
  const items = [
    { icon: Atom, title: "Quantum-Ready QUBO Engine", desc: "Transform portfolio optimization problems into scalable QUBO formulations compatible with hybrid computational systems." },
    { icon: Brain, title: "Hybrid Solver Intelligence", desc: "Combine classical optimization, quantum-inspired methods, and advanced heuristics for adaptive execution." },
    { icon: BarChart3, title: "Advanced Risk Analytics", desc: "Model risk-return balancing using intelligent computational finance architectures and dynamic constraints." },
    { icon: Cloud, title: "Cloud Quantum Infrastructure", desc: "Future-ready integration with AWS Braket, D-Wave Leap, IBM Quantum, and distributed optimization pipelines." },
    { icon: Zap, title: "Real-Time Optimization", desc: "Enable dynamic computational portfolio analysis with scalable execution and real-time adaptation." },
    { icon: Sparkles, title: "Computational Visualization", desc: "Interactive financial visualization powered by WebGL, advanced motion systems, and intelligence layers." },
  ];

  return (
    <section id="features" className="relative py-32">
      <div className="absolute inset-0 bg-aurora opacity-50 pointer-events-none" />
      <div className="relative mx-auto max-w-7xl px-6">
        <div className="max-w-3xl">
          <SectionLabel>Designed For</SectionLabel>
          <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.75rem)] font-medium leading-[1.05] tracking-[-0.02em]">
            Intelligent <span className="text-gradient-quantum">computational finance</span>.
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((it, i) => (
            <motion.div
              key={it.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.7, delay: i * 0.06, ease }}
              className="group relative"
            >
              <TiltCard>
                <div className="glass-card border-glow rounded-2xl p-7 h-full transition-all duration-500 hover:bg-card/60 hover:-translate-y-1 hover:shadow-[0_30px_80px_-30px_oklch(0.65_0.27_295/40%)] transform-gpu will-change-transform" style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}>
                  <div className="relative h-11 w-11 rounded-xl bg-gradient-to-br from-primary/30 to-accent/20 grid place-items-center mb-6 border border-primary/30">
                    <div className="absolute inset-0 rounded-xl bg-primary/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity" />
                    <it.icon className="relative h-5 w-5 text-primary" strokeWidth={1.5} />
                  </div>
                  <h3 className="font-display text-lg font-medium tracking-tight">{it.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{it.desc}</p>
                </div>
              </TiltCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}


/* ============== ANALYTICS ============== */
function Analytics() {
  const kpis = [
    { v: "12.4x", l: "Optimization Speed", s: "Faster Execution" },
    { v: "94.7%", l: "Portfolio Efficiency", s: "Efficiency Score" },
    { v: "99.8%", l: "Computational Accuracy", s: "Accuracy Rate" },
    { v: "98.3%", l: "Solver Performance", s: "Performance Index" },
    { v: "100%", l: "Quantum Compatibility", s: "Ready" },
  ];

  // Generate mock chart paths
  const generatePath = (seed: number, amp = 30) => {
    const points: string[] = [];
    for (let i = 0; i <= 60; i++) {
      const x = (i / 60) * 100;
      const y = 50 - Math.sin(i * 0.3 + seed) * amp * 0.5 + Math.cos(i * 0.15 + seed) * amp * 0.3 - i * 0.4;
      points.push(`${x},${y}`);
    }
    return `M${points.join(" L")}`;
  };

  return (
    <section className="relative py-32 flex flex-col gap-16">
      {/* Background diagram placed behind this section */}
      <div className="absolute inset-0 -z-10 opacity-30">
        <ArchitectureDiagram />
      </div>
      <div className="relative z-10 mx-auto max-w-7xl px-6 w-full">
        <div className="max-w-3xl">
          <SectionLabel>Optimization Backed By</SectionLabel>
          <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.02em]">
            <span className="text-gradient-quantum">Computational</span> intelligence.
          </h2>
        </div>

        <div className="mt-14 grid grid-cols-2 md:grid-cols-5 gap-3">
          {kpis.map((k, i) => (
            <motion.div
              key={k.l}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="glass-card rounded-2xl p-5 transform-gpu will-change-transform"
              style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}
            >
              <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{k.l}</div>
              <div className="font-display text-2xl md:text-3xl font-medium text-gradient-quantum mt-2">{k.v}</div>
              <div className="text-[10px] text-muted-foreground mt-1">{k.s}</div>
            </motion.div>
          ))}
        </div>

        <div className="mt-6 grid lg:grid-cols-2 gap-4">
          {/* Performance chart */}
          <div className="glass-card rounded-2xl p-6 transform-gpu will-change-transform" style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="font-display font-medium">Portfolio Performance</div>
                <div className="text-xs text-muted-foreground mt-0.5">Cumulative return · 12 months</div>
              </div>
              <div className="flex gap-3 text-[10px] font-mono">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" />Quantum-Hybrid</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-accent" />Classical</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-muted-foreground" />Traditional</span>
              </div>
            </div>
            <svg viewBox="0 0 100 60" className="w-full h-48" preserveAspectRatio="none">
              <defs>
                <linearGradient id="g1" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.65 0.27 295)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="oklch(0.65 0.27 295)" stopOpacity="0" />
                </linearGradient>
              </defs>
              {[10, 20, 30, 40, 50].map((y) => (
                <line key={y} x1="0" x2="100" y1={y} y2={y} stroke="oklch(1 0 0 / 5%)" strokeWidth="0.2" />
              ))}
              <path d={`${generatePath(0, 35)} L100,60 L0,60 Z`} fill="url(#g1)" />
              <path d={generatePath(0, 35)} stroke="oklch(0.7 0.27 295)" strokeWidth="0.6" fill="none" />
              <path d={generatePath(2, 22)} stroke="oklch(0.7 0.22 245)" strokeWidth="0.5" fill="none" opacity="0.8" />
              <path d={generatePath(4, 12)} stroke="oklch(0.6 0.04 270)" strokeWidth="0.4" fill="none" opacity="0.6" />
            </svg>
          </div>

          {/* Allocation donut */}
          <div className="glass-card rounded-2xl p-6 transform-gpu will-change-transform" style={{ WebkitBackdropFilter: 'blur(10px) translateZ(0)' }}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="font-display font-medium">Allocation Distribution</div>
                <div className="text-xs text-muted-foreground mt-0.5">Sector exposure breakdown</div>
              </div>
            </div>
            <div className="flex items-center gap-8">
              <svg viewBox="0 0 100 100" className="h-48 w-48 -rotate-90">
                {[
                  { v: 28.5, c: "oklch(0.7 0.27 295)" },
                  { v: 22.1, c: "oklch(0.7 0.22 245)" },
                  { v: 18.7, c: "oklch(0.78 0.18 200)" },
                  { v: 16.3, c: "oklch(0.6 0.2 320)" },
                  { v: 8.9, c: "oklch(0.55 0.15 270)" },
                  { v: 5.5, c: "oklch(0.45 0.08 270)" },
                ].reduce<React.ReactElement[]>((acc, seg, i, arr) => {
                  const start = arr.slice(0, i).reduce((a, s) => a + s.v, 0);
                  const c = 2 * Math.PI * 35;
                  acc.push(
                    <circle
                      key={i}
                      cx="50" cy="50" r="35" fill="none"
                      stroke={seg.c} strokeWidth="14"
                      strokeDasharray={`${(seg.v / 100) * c} ${c}`}
                      strokeDashoffset={-((start / 100) * c)}
                    />
                  );
                  return acc;
                }, [])}
              </svg>
              <div className="flex-1 space-y-2 text-xs">
                {[
                  { l: "Technology", v: "28.5%", c: "oklch(0.7 0.27 295)" },
                  { l: "Healthcare", v: "22.1%", c: "oklch(0.7 0.22 245)" },
                  { l: "Finance", v: "18.7%", c: "oklch(0.78 0.18 200)" },
                  { l: "Energy", v: "16.3%", c: "oklch(0.6 0.2 320)" },
                  { l: "Consumer", v: "8.9%", c: "oklch(0.55 0.15 270)" },
                  { l: "Other", v: "5.5%", c: "oklch(0.45 0.08 270)" },
                ].map((r) => (
                  <div key={r.l} className="flex items-center justify-between">
                    <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ background: r.c }} />{r.l}</span>
                    <span className="font-mono text-muted-foreground">{r.v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quantum vs Classical bars */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="font-display font-medium">Quantum vs Classical</div>
                <div className="text-xs text-muted-foreground mt-0.5">Solver benchmark · normalized score</div>
              </div>
              <div className="text-right">
                <div className="font-mono text-xs text-primary">+37.5% avg advantage</div>
                <div className="flex gap-3 text-[10px] font-mono mt-2 justify-end">
                  <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-gradient-to-t from-primary to-accent" />Quantum</span>
                  <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-muted-foreground/40" />Classical</span>
                </div>
              </div>
            </div>
            {(() => {
              const metrics = [
                { l: "Sharpe", q: 92, c: 67 },
                { l: "Speed", q: 95, c: 42 },
                { l: "Risk-Adj", q: 88, c: 71 },
                { l: "Diversity", q: 84, c: 76 },
                { l: "Drawdown", q: 90, c: 58 },
                { l: "Convergence", q: 96, c: 49 },
              ];
              return (
                <div className="relative pl-8">
                  {/* Y axis ticks */}
                  <div className="absolute left-0 top-0 h-44 flex flex-col justify-between text-[9px] font-mono text-muted-foreground/60">
                    <span>100</span><span>75</span><span>50</span><span>25</span><span>0</span>
                  </div>
                  {/* Gridlines */}
                  <div className="relative h-44">
                    {[0, 25, 50, 75, 100].map((g) => (
                      <div key={g} className="absolute left-0 right-0 border-t border-border/30" style={{ bottom: `${g}%` }} />
                    ))}
                    <div className="absolute inset-0 flex items-end gap-3">
                      {metrics.map((m) => (
                        <div key={m.l} className="flex-1 flex items-end justify-center gap-1 h-full">
                          <div
                            className="w-1/2 rounded-t bg-gradient-to-t from-primary to-accent shadow-[0_0_20px_-4px_oklch(0.65_0.27_295/60%)]"
                            style={{ height: `${m.q}%` }}
                            title={`Quantum: ${m.q}`}
                          />
                          <div
                            className="w-1/2 rounded-t bg-muted-foreground/30"
                            style={{ height: `${m.c}%` }}
                            title={`Classical: ${m.c}`}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  {/* X labels */}
                  <div className="flex gap-3 mt-2">
                    {metrics.map((m) => (
                      <div key={m.l} className="flex-1 text-center text-[10px] font-mono text-muted-foreground">{m.l}</div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Heatmap */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="font-display font-medium">Nifty 50 Correlation Matrix</div>
                <div className="text-xs text-muted-foreground mt-0.5">Daily return ρ · NSE · trailing 2Y</div>
              </div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                <span>0</span>
                <span className="h-2 w-24 rounded-full" style={{ background: "linear-gradient(90deg, oklch(0.22 0.02 270), oklch(0.45 0.15 270), oklch(0.7 0.27 295))" }} />
                <span>+1</span>
              </div>
            </div>
            {(() => {
              const assets = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "BHARTIARTL"];
              // Real-world approximate daily-return correlations for Nifty 50 large caps (trailing ~2Y NSE data)
              const M: number[][] = [
                [1.00, 0.32, 0.30, 0.45, 0.48, 0.42, 0.35, 0.55, 0.38],
                [0.32, 1.00, 0.86, 0.38, 0.36, 0.30, 0.28, 0.40, 0.34],
                [0.30, 0.86, 1.00, 0.36, 0.34, 0.28, 0.26, 0.38, 0.32],
                [0.45, 0.38, 0.36, 1.00, 0.78, 0.62, 0.40, 0.52, 0.42],
                [0.48, 0.36, 0.34, 0.78, 1.00, 0.72, 0.42, 0.55, 0.44],
                [0.42, 0.30, 0.28, 0.62, 0.72, 1.00, 0.38, 0.50, 0.40],
                [0.35, 0.28, 0.26, 0.40, 0.42, 0.38, 1.00, 0.36, 0.32],
                [0.55, 0.40, 0.38, 0.52, 0.55, 0.50, 0.36, 1.00, 0.45],
                [0.38, 0.34, 0.32, 0.42, 0.44, 0.40, 0.32, 0.45, 1.00],
              ];
              const colorFor = (v: number) => {
                const a = Math.max(0, Math.min(1, v));
                const chroma = 0.04 + a * 0.24;
                const light = 0.20 + a * 0.50;
                const hue = 245 + a * 50;
                return `oklch(${light} ${chroma} ${hue})`;
              };
              return (
                <div className="grid gap-[3px]" style={{ gridTemplateColumns: `minmax(70px,auto) repeat(${assets.length}, minmax(0,1fr))` }}>
                  <div />
                  {assets.map((a) => (
                    <div key={`h-${a}`} className="text-[8px] font-mono text-muted-foreground text-center truncate" title={a}>{a.slice(0, 5)}</div>
                  ))}
                  {assets.map((rowA, i) => (
                    <React.Fragment key={`row-${rowA}`}>
                      <div className="text-[9px] font-mono text-muted-foreground pr-2 flex items-center justify-end truncate" title={rowA}>{rowA}</div>
                      {assets.map((colA, j) => {
                        const v = M[i][j];
                        return (
                          <div
                            key={`c-${i}-${j}`}
                            className="aspect-square rounded-sm grid place-items-center text-[8px] font-mono text-foreground/85 border border-border/20"
                            style={{ background: colorFor(v) }}
                            title={`${rowA} / ${colA}: ${v.toFixed(2)}`}
                          >
                            {v >= 0.6 ? v.toFixed(2) : ""}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
              );
            })()}
          </div>

        </div>
      </div>
    </section>
  );
}

/* ============== ECOSYSTEM ============== */
function Ecosystem() {
  const cats = [
    { title: "Frontend Systems", items: ["Next.js", "React", "TailwindCSS", "Framer Motion", "GSAP", "Three.js"] },
    { title: "Quantum & Optimization", items: ["D-Wave Ocean SDK", "IBM Qiskit", "AWS Braket", "QUBO Modeling", "Hybrid Optimization"] },
    { title: "Backend Infrastructure", items: ["Python", "FastAPI", "NumPy", "Pandas", "PostgreSQL"] },
  ];
  const icons = [Layers, Cpu, Network];

  return (
    <section className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-3xl">
          <SectionLabel>Powered By</SectionLabel>
          <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.02em]">
            Advanced <span className="text-gradient-quantum">computational technologies</span>.
          </h2>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-5">
          {cats.map((c, i) => {
            const Icon = icons[i];
            return (
              <motion.div
                key={c.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: i * 0.1 }}
                className="glass-card border-glow rounded-2xl p-7 hover:-translate-y-1 transition-all"
              >
                <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-primary/30 to-accent/20 grid place-items-center border border-primary/30 mb-5">
                  <Icon className="h-5 w-5 text-primary" strokeWidth={1.5} />
                </div>
                <h3 className="font-display text-lg font-medium">{c.title}</h3>
                <ul className="mt-5 space-y-2">
                  {c.items.map((it) => (
                    <li key={it} className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span className="h-1 w-1 rounded-full bg-primary" />{it}
                    </li>
                  ))}
                </ul>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ============== FUTURE VISION ============== */
function Vision() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [50, -50]);

  const items = [
    "Quantum Hardware Integration",
    "GPU-Accelerated Optimization",
    "Distributed Compute Systems",
    "AI-Driven Intelligence",
    "Live Market Integration",
  ];

  return (
    <section ref={ref} className="relative py-32 overflow-hidden">
      <motion.div style={{ y }} className="absolute inset-0 bg-aurora opacity-60">
        <div className="absolute inset-0 grid-bg" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-background" />
      </motion.div>


      <div className="relative mx-auto max-w-7xl px-6 grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <SectionLabel>Scaling Toward The Future Of</SectionLabel>
          <h2 className="font-display mt-6 text-[clamp(2rem,5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.02em]">
            <span className="text-gradient-quantum">Computational</span> finance.
          </h2>
          <p className="mt-6 text-muted-foreground leading-relaxed max-w-lg">
            QURVE establishes the foundation for next-generation computational finance through
            hybrid quantum-classical optimization, scalable intelligence systems, and future-ready
            financial architectures.
          </p>
          <MagneticButton>
            <a href="#cta" className="mt-8 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary/90 to-accent/90 px-5 py-3 text-sm font-medium glow-sm hover:shadow-[0_0_50px_-8px_oklch(0.65_0.27_295/80%)] transition-shadow">
              Explore Roadmap <ArrowRight className="h-4 w-4" />
            </a>
          </MagneticButton>
        </div>

        <div className="space-y-3">
          {items.map((it, i) => (
            <motion.div
              key={it}
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="glass-card rounded-xl p-5 flex items-center gap-4 hover:border-primary/40 transition-colors"
            >
              <div className="font-mono text-xs text-primary/70 w-8">0{i + 1}</div>
              <div className="flex-1 font-display font-medium">{it}</div>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============== FINAL CTA ============== */
function FinalCTA() {
  return (
    <section id="cta" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 bg-aurora opacity-80">
        <div className="absolute inset-0 grid-bg opacity-50" />
        <div className="absolute inset-0 bg-gradient-to-b from-background via-background/40 to-background" />
      </div>

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/30 blur-[150px] animate-pulse-glow" />

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <SectionLabel>Building The Future Of</SectionLabel>
        <h2 className="font-display mt-8 text-[clamp(2.5rem,7vw,5rem)] font-medium leading-[1.02] tracking-[-0.03em]">
          <span className="text-gradient-quantum">Quantum</span>
          <br />
          finance.
        </h2>
        <p className="mt-8 text-lg text-muted-foreground max-w-xl mx-auto">
          Experience computational finance reimagined through hybrid quantum-classical
          intelligence and cinematic interactive systems.
        </p>
        <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
          <MagneticButton>
            <Link to="/login" className="group inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary via-primary to-accent px-7 py-4 text-sm font-medium shadow-[0_0_60px_-10px_oklch(0.65_0.27_295/90%)] hover:scale-[1.03] transition-transform">
              Launch Platform <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </MagneticButton>
          <MagneticButton>
            <a href="#" className="inline-flex items-center gap-2 rounded-full border border-border bg-card/40 backdrop-blur px-7 py-4 text-sm font-medium hover:bg-card/70 transition-colors">
              <Github className="h-4 w-4" /> View GitHub
            </a>
          </MagneticButton>
        </div>
      </div>
    </section>
  );
}

/* ============== FOOTER ============== */
function Footer() {
  return (
    <footer className="relative border-t border-border/40 py-12">
      <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2.5">
          <div className="h-6 w-6 rounded-full bg-gradient-to-br from-primary to-accent" />
          <span className="font-display font-semibold tracking-tight">QURVE</span>
          <span className="text-xs text-muted-foreground ml-3">© 2026 — Quantum Portfolio Intelligence</span>
        </div>
        <div className="flex items-center gap-6 text-xs text-muted-foreground">
          <a href="#" className="hover:text-foreground">Privacy</a>
          <a href="#" className="hover:text-foreground">Terms</a>
          <a href="#" className="hover:text-foreground">Security</a>
          <a href="#" className="hover:text-foreground">Docs</a>
        </div>
      </div>
    </footer>
  );
}

export default function Landing() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <Nav />
      <main>
        <Hero />
        <TechStrip />
        <Features />
        <ScrollStory />
        <Analytics />
        <Ecosystem />
        <Vision />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
