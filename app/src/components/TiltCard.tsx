import { useRef, useCallback, useState } from "react";
import { gsap } from "gsap";

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  intensity?: number;
}

export function TiltCard({
  children,
  className = "",
  intensity = 8,
}: TiltCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [lightPos, setLightPos] = useState({ x: 50, y: 50 });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const ratioX = (e.clientX - centerX) / (rect.width / 2);
      const ratioY = (e.clientY - centerY) / (rect.height / 2);

      // Rotate inversely for natural tilt feel
      gsap.to(cardRef.current, {
        rotateY: ratioX * intensity,
        rotateX: -ratioY * intensity,
        duration: 0.4,
        ease: "power2.out",
      });

      // Light follow
      const px = ((e.clientX - rect.left) / rect.width) * 100;
      const py = ((e.clientY - rect.top) / rect.height) * 100;
      setLightPos({ x: px, y: py });
    },
    [intensity]
  );

  const handleMouseLeave = useCallback(() => {
    if (!cardRef.current) return;
    gsap.to(cardRef.current, {
      rotateX: 0,
      rotateY: 0,
      duration: 0.6,
      ease: "power3.out",
    });
    setLightPos({ x: 50, y: 50 });
  }, []);

  return (
    <div
      style={{ perspective: 1000, transformStyle: "preserve-3d" }}
      className={className}
    >
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative will-change-transform"
        style={{ transformStyle: "preserve-3d" }}
      >
        {children}
        {/* Cursor-follow light */}
        <div
          className="pointer-events-none absolute inset-0 rounded-[inherit] transition-opacity duration-500"
          style={{
            background: `radial-gradient(circle at ${lightPos.x}% ${lightPos.y}%, oklch(0.65 0.27 295 / 12%) 0%, transparent 60%)`,
            opacity: lightPos.x !== 50 || lightPos.y !== 50 ? 1 : 0,
          }}
        />
      </div>
    </div>
  );
}
