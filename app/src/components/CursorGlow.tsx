import { useEffect, useRef, useState } from "react";

export function CursorGlow() {
  const dotRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const mousePos = useRef({ x: -100, y: -100 });
  const glowPos = useRef({ x: -100, y: -100 });
  const [isVisible, setIsVisible] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    // Only show on pointer devices (not touch)
    const hasPointer = window.matchMedia("(pointer: fine)").matches;
    if (!hasPointer) return;

    setIsVisible(true);

    const handleMove = (e: MouseEvent) => {
      mousePos.current.x = e.clientX;
      mousePos.current.y = e.clientY;
      // Dot follows immediately
      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${e.clientX - 3}px, ${e.clientY - 3}px) scale(${isPressed ? 0.7 : 1})`;
      }
    };

    const handleDown = () => setIsPressed(true);
    const handleUp = () => setIsPressed(false);

    // Glow follows with lerp
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
    const animate = () => {
      glowPos.current.x = lerp(glowPos.current.x, mousePos.current.x, 0.08);
      glowPos.current.y = lerp(glowPos.current.y, mousePos.current.y, 0.08);
      if (glowRef.current) {
        glowRef.current.style.transform = `translate(${glowPos.current.x - 25}px, ${glowPos.current.y - 25}px)`;
      }
      rafRef.current = requestAnimationFrame(animate);
    };

    document.addEventListener("mousemove", handleMove, { passive: true });
    document.addEventListener("mousedown", handleDown);
    document.addEventListener("mouseup", handleUp);
    rafRef.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mousedown", handleDown);
      document.removeEventListener("mouseup", handleUp);
      cancelAnimationFrame(rafRef.current);
    };
  }, [isPressed]);

  if (!isVisible) return null;

  return (
    <>
      {/* Dot */}
      <div
        ref={dotRef}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: "oklch(0.9 0.1 295)",
          pointerEvents: "none",
          zIndex: 99999,
          willChange: "transform",
          transition: "transform 0.05s linear",
          mixBlendMode: "difference",
        }}
      />
      {/* Trailing glow */}
      <div
        ref={glowRef}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: 50,
          height: 50,
          borderRadius: "50%",
          background: "radial-gradient(circle, oklch(0.65 0.27 295 / 30%) 0%, transparent 70%)",
          pointerEvents: "none",
          zIndex: 99998,
          willChange: "transform",
          mixBlendMode: "screen",
        }}
      />
    </>
  );
}
