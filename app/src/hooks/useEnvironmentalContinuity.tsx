import { useState, useEffect } from 'react';
import { useScroll, useTransform } from 'framer-motion';

// Environmental continuity system for persistent visual elements
export const useEnvironmentalContinuity = () => {
  const [glowIntensity, setGlowIntensity] = useState(0.3);
  const [atmosphereHue, setAtmosphereHue] = useState(250); // Deep purple to electric blue range
  const [floatingElements, setFloatingElements] = useState<Array<{id: string; x: number; y: number; delay: number}>>([]);
  
  const { scrollYProgress } = useScroll();
  
  // Evolve atmosphere based on scroll - deeper purple to electric blue
  const atmosphereEvolution = useTransform(scrollYProgress, [0, 1], [250, 200], {
    clamp: true
  });
  
  const glowEvolution = useTransform(scrollYProgress, [0, 1], [0.3, 0.6], {
    clamp: true
  });
  
  // Create persistent floating elements
  useEffect(() => {
    const elements: Array<{id: string; x: number; y: number; delay: number}> = [
      { id: 'orb-fragment-1', x: 20, y: 15, delay: 0 },
      { id: 'orb-fragment-2', x: 80, y: 25, delay: 0.5 },
      { id: 'orb-fragment-3', x: 15, y: 60, delay: 1 },
      { id: 'data-stream-1', x: 70, y: 20, delay: 1.5 },
      { id: 'data-stream-2', x: 25, y: 45, delay: 2 },
    ];
    
    setFloatingElements(elements);
  }, []);
  
  // Update atmospheric values with ultra-aggressive throttling for buttery smooth scrolling
  useEffect(() => {
    let animationFrameId: number;
    let lastUpdate = 0;
    const throttleMs = 100; // ~10fps for maximum performance
    let scrollTimeout: NodeJS.Timeout;
    let isScrolling = false;
    let lastScrollY = 0;
    let scrollDirection = 'none';
    
    const throttledUpdate = (timestamp: number) => {
      if (timestamp - lastUpdate >= throttleMs && isScrolling) {
        // Only update when scrolling down to prevent lag
        if (scrollDirection === 'down') {
          setAtmosphereHue(atmosphereEvolution.get());
          setGlowIntensity(glowEvolution.get());
        }
        lastUpdate = timestamp;
      }
      animationFrameId = requestAnimationFrame(throttledUpdate);
    };
    
    // Ultra-aggressive scroll detection with direction
    const handleScrollStart = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY) {
        scrollDirection = 'down';
      } else if (currentScrollY < lastScrollY) {
        scrollDirection = 'up';
      }
      lastScrollY = currentScrollY;
      isScrolling = true;
      clearTimeout(scrollTimeout);
    };
    
    // Debounce scroll end for smooth experience
    const handleScrollEnd = () => {
      isScrolling = false;
      scrollDirection = 'none';
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        setAtmosphereHue(atmosphereEvolution.get());
        setGlowIntensity(glowEvolution.get());
      }, 200);
    };
    
    // Start animation loop
    animationFrameId = requestAnimationFrame(throttledUpdate);
    
    // Add ultra-optimized scroll listeners
    window.addEventListener('scroll', handleScrollStart, { passive: true, capture: false });
    window.addEventListener('scrollend', handleScrollEnd, { passive: true });
    window.addEventListener('touchstart', handleScrollStart, { passive: true });
    window.addEventListener('touchend', handleScrollEnd, { passive: true });
    
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      clearTimeout(scrollTimeout);
      window.removeEventListener('scroll', handleScrollStart);
      window.removeEventListener('scrollend', handleScrollEnd);
      window.removeEventListener('touchstart', handleScrollStart);
      window.removeEventListener('touchend', handleScrollEnd);
    };
  }, [atmosphereEvolution, glowEvolution]);
  
  return {
    glowIntensity,
    atmosphereHue,
    floatingElements,
    scrollProgress: scrollYProgress.get()
  };
};
