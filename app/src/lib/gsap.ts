import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Register plugins once
gsap.registerPlugin(ScrollTrigger);

// Default easing — Apple-grade smooth
export const EASE = {
  smooth: "power3.out",
  cinematic: "power4.out",
  spring: "elastic.out(1, 0.5)",
  expo: "expo.out",
  quint: [0.22, 1, 0.36, 1] as const,
} as const;

// Shared scrub config for scroll-linked animations
export const SCRUB_CONFIG = {
  smooth: { scrub: 1 },
  tight: { scrub: 0.5 },
  loose: { scrub: 2 },
} as const;

export { gsap, ScrollTrigger };
