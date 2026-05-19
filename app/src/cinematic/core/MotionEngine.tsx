import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { motion, useMotionValue } from 'framer-motion';
import { useExperience } from './ExperienceDirector';

// Motion state interface
export interface MotionState {
  globalVelocity: { x: number; y: number };
  scrollVelocity: number;
  isInteracting: boolean;
  momentum: number;
  intensity: number;
  damping: number;
  stiffness: number;
  mass: number;
}

// Motion presets for different behaviors
export enum MotionPreset {
  SUBTLE = 'subtle',
  NATURAL = 'natural',
  RESPONSIVE = 'responsive',
  CINEMATIC = 'cinematic',
  AGGRESSIVE = 'aggressive'
}

// Context for global motion management
const MotionContext = createContext<{
  state: MotionState;
  setPreset: (preset: MotionPreset) => void;
  addForce: (force: { x: number; y: number }) => void;
  setIntensity: (intensity: number) => void;
  getSpringConfig: () => { stiffness: number; damping: number; mass: number };
} | null>(null);

export const useMotion = () => {
  const context = useContext(MotionContext);
  if (!context) throw new Error('useMotion must be used within MotionProvider');
  return context;
};

interface MotionProviderProps {
  children: React.ReactNode;
}

export const MotionProvider: React.FC<MotionProviderProps> = ({ children }) => {
    const animationFrameRef = useRef<number | undefined>(undefined);
  // Disable dynamic motion for performance
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const lastVelocityRef = useRef({ x: 0, y: 0 });
  const forcesRef = useRef<Array<{ x: number; y: number; decay: number }>>([]);
  
  const [state, setState] = useState<MotionState>({
    globalVelocity: { x: 0, y: 0 },
    scrollVelocity: 0,
    isInteracting: false,
    momentum: 0,
    intensity: 0.5,
    damping: 20,
    stiffness: 100,
    mass: 1
  });

  // Motion springs are removed to avoid unused variables

  // Mouse/touch interaction tracking
  useEffect(() => {
    const handleInteraction = (e: MouseEvent | TouchEvent) => {
      if (e.type === 'mousemove' || e.type === 'touchmove') {
        const clientX = 'touches' in e ? e.touches[0]?.clientX || 0 : e.clientX;
        const clientY = 'touches' in e ? e.touches[0]?.clientY || 0 : e.clientY;
        
        const velocityX = (clientX - lastVelocityRef.current.x) * 0.1;
        const velocityY = (clientY - lastVelocityRef.current.y) * 0.1;
        
        lastVelocityRef.current = { x: clientX, y: clientY };
        
        setState(prev => ({
          ...prev,
          globalVelocity: {
            x: prev.globalVelocity.x + velocityX,
            y: prev.globalVelocity.y + velocityY
          },
          isInteracting: true
        }));
      }
    };

    const handleInteractionEnd = () => {
      setState(prev => ({ ...prev, isInteracting: false }));
    };

    window.addEventListener('mousemove', handleInteraction);
    window.addEventListener('touchmove', handleInteraction);
    window.addEventListener('mouseup', handleInteractionEnd);
    window.addEventListener('touchend', handleInteractionEnd);

    return () => {
      window.removeEventListener('mousemove', handleInteraction);
      window.removeEventListener('touchmove', handleInteraction);
      window.removeEventListener('mouseup', handleInteractionEnd);
      window.removeEventListener('touchend', handleInteractionEnd);
    };
  }, []);

  // Force accumulation and decay system
  useEffect(() => {
    const updateForces = () => {
      // Decay existing forces
      forcesRef.current = forcesRef.current
        .map(force => ({ ...force, decay: force.decay * 0.95 }))
        .filter(force => force.decay > 0.01);

      // Apply accumulated forces to velocity
      const totalForce = forcesRef.current.reduce(
        (acc, force) => ({ x: acc.x + force.x * force.decay, y: acc.y + force.y * force.decay }),
        { x: 0, y: 0 }
      );

      if (totalForce.x !== 0 || totalForce.y !== 0) {
        setState(prev => ({
          ...prev,
          globalVelocity: {
            x: prev.globalVelocity.x + totalForce.x,
            y: prev.globalVelocity.y + totalForce.y
          }
        }));
      }

      requestAnimationFrame(updateForces);
    };

    updateForces();
  }, []);

  // Motion preset configurations
  const setPreset = (preset: MotionPreset) => {
    const presets = {
      [MotionPreset.SUBTLE]: { stiffness: 60, damping: 25, mass: 1.2 },
      [MotionPreset.NATURAL]: { stiffness: 100, damping: 20, mass: 1 },
      [MotionPreset.RESPONSIVE]: { stiffness: 150, damping: 15, mass: 0.8 },
      [MotionPreset.CINEMATIC]: { stiffness: 80, damping: 18, mass: 1.5 },
      [MotionPreset.AGGRESSIVE]: { stiffness: 200, damping: 12, mass: 0.6 }
    };

    const config = presets[preset];
    if (config) {
      setState(prev => ({ ...prev, ...config }));
    }
  };

  // Add external force to motion system
  const addForce = (force: { x: number; y: number }) => {
    forcesRef.current.push({ ...force, decay: 1 });
  };

  // Set motion intensity
  const setIntensity = (intensity: number) => {
    setState(prev => ({
      ...prev,
      intensity: Math.max(0, Math.min(1, intensity))
    }));
  };

  // Get spring configuration for components
  const getSpringConfig = () => ({
    stiffness: state.stiffness,
    damping: state.damping,
    mass: state.mass
  });

  return (
    <MotionContext.Provider value={{
      state,
      setPreset,
      addForce,
      setIntensity,
      getSpringConfig
    }}>
      <motion.div
        className="motion-engine"
        style={{
          // Apply subtle global motion based on velocity
          transform: `translate(${state.globalVelocity.x * 0.5}px, ${state.globalVelocity.y * 0.5}px)`,
          filter: state.intensity > 0.7 ? `blur(${state.intensity * 0.5}px)` : 'none'
        }}
      >
        {children}
      </motion.div>
    </MotionContext.Provider>
  );
};

// Hook for component-specific motion
export const useComponentMotion = () => {
  const { state, addForce, setIntensity, getSpringConfig } = useMotion();
  
  const createFloatingMotion = (intensity?: number) => ({
    animate: {
      y: [0, -15 * (intensity || state.intensity), 0],
      rotate: [0, 1.5 * (intensity || state.intensity), 0],
      scale: [1, 1.02 * (intensity || state.intensity), 1]
    },
    transition: {
      duration: 8,
      repeat: Infinity,
      ease: "easeInOut" as const
    }
  });

  const createVelocityReaction = () => ({
    animate: {
      x: state.globalVelocity.x * state.intensity * 2,
      y: state.globalVelocity.y * state.intensity * 2,
      scale: 1 + (state.scrollVelocity * 0.01)
    },
    transition: {
      type: "spring",
      ...getSpringConfig()
    }
  });

  const createHoverMotion = () => ({
    whileHover: {
      scale: 1.05,
      transition: { ...getSpringConfig() }
    },
    whileTap: {
      scale: 0.98,
      transition: { ...getSpringConfig() }
    }
  });

  return {
    state,
    addForce,
    setIntensity,
    getSpringConfig,
    createFloatingMotion,
    createVelocityReaction,
    createHoverMotion
  };
};

// Hook for scroll-based animations
export const useScrollMotion = () => {
  const { state } = useExperience();
  const motion = useComponentMotion();
  
  const createScrollReveal = (delay?: number) => ({
    initial: { opacity: 0, y: 50 },
    whileInView: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.7,
        delay: delay || 0,
        ...motion.getSpringConfig()
      }
    },
    viewport: { once: true, margin: "-100px" }
  });

  const createParallaxMotion = (speed?: number) => ({
    style: {
      y: useMotionValue(0)
    },
    animate: {
      y: state.scrollProgress * (speed || 100) * -1
    }
  });

  return {
    createScrollReveal,
    createParallaxMotion
  };
};
