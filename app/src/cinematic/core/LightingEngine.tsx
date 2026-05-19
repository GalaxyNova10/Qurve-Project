import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

// Lighting state interface
export interface LightingState {
  ambientIntensity: number;
  directionalIntensity: number;
  colorTemperature: number; // 0 = cool, 1 = warm
  bloomStrength: number;
  volumetricDensity: number;
  shadowSoftness: number;
  cursorLightX: number;
  cursorLightY: number;
  isReactive: boolean;
  pulsePhase: number;
}

// Lighting presets for different moods
export enum LightingPreset {
  CYBERPUNK = 'cyberpunk',
  ATMOSPHERIC = 'atmospheric',
  CLINICAL = 'clinical',
  CINEMATIC = 'cinematic',
  INTIMATE = 'intimate'
}

// Context for global lighting management
const LightingContext = createContext<{
  state: LightingState;
  setPreset: (preset: LightingPreset) => void;
  updateCursorLight: (x: number, y: number) => void;
  setIntensity: (intensity: number) => void;
  triggerPulse: () => void;
  getLightingCSS: () => React.CSSProperties;
} | null>(null);

export const useLighting = () => {
  const context = useContext(LightingContext);
  if (!context) throw new Error('useLighting must be used within LightingProvider');
  
  // Add missing methods for component usage
  const createGlowEffect = (intensity?: number) => ({
    style: {
      boxShadow: `
        0 0 ${20 * (intensity || context.state.ambientIntensity)}px rgba(124, 58, 237, 0.3),
        0 0 ${40 * (intensity || context.state.ambientIntensity)}px rgba(124, 58, 237, 0.1)
      `,
      filter: `brightness(${1 + context.state.bloomStrength * 0.2})`
    }
  });

  const createReactiveGlow = () => ({
    whileHover: {
      boxShadow: `
        0 0 ${30 * context.state.ambientIntensity}px rgba(124, 58, 237, 0.5),
        0 0 ${60 * context.state.ambientIntensity}px rgba(124, 58, 237, 0.2)
      `,
      transition: { duration: 0.3 }
    },
    onTap: () => context.triggerPulse()
  });

  return {
    ...context,
    createGlowEffect,
    createReactiveGlow
  };
};

interface LightingProviderProps {
  children: React.ReactNode;
}

export const LightingProvider: React.FC<LightingProviderProps> = ({ children }) => {
    const animationFrameRef = useRef<number | undefined>(undefined);
  const pulseTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  
  const [state, setState] = useState<LightingState>({
    ambientIntensity: 0.7,
    directionalIntensity: 0.5,
    colorTemperature: 0.3, // Cool blue/purple
    bloomStrength: 0.4,
    volumetricDensity: 0.3,
    shadowSoftness: 0.8,
    cursorLightX: 0.5,
    cursorLightY: 0.5,
    isReactive: true,
    pulsePhase: 0
  });

  // Disable dynamic lighting for performance
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Cursor-reactive lighting
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (state.isReactive) {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;
        
        setState(prev => ({
          ...prev,
          cursorLightX: x,
          cursorLightY: y
        }));
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [state.isReactive]);

  // Pulse animation system
  useEffect(() => {
    const interval = setInterval(() => {
      setState(prev => ({
        ...prev,
        pulsePhase: (prev.pulsePhase + 0.05) % (Math.PI * 2)
      }));
    }, 50);

    return () => clearInterval(interval);
  }, []);

  // Lighting preset configurations
  const setPreset = (preset: LightingPreset) => {
    const presets = {
      [LightingPreset.CYBERPUNK]: {
        ambientIntensity: 0.6,
        directionalIntensity: 0.8,
        colorTemperature: 0.2,
        bloomStrength: 0.7,
        volumetricDensity: 0.4,
        shadowSoftness: 0.6
      },
      [LightingPreset.ATMOSPHERIC]: {
        ambientIntensity: 0.8,
        directionalIntensity: 0.4,
        colorTemperature: 0.5,
        bloomStrength: 0.5,
        volumetricDensity: 0.6,
        shadowSoftness: 0.9
      },
      [LightingPreset.CLINICAL]: {
        ambientIntensity: 0.9,
        directionalIntensity: 0.7,
        colorTemperature: 0.7,
        bloomStrength: 0.2,
        volumetricDensity: 0.1,
        shadowSoftness: 0.3
      },
      [LightingPreset.CINEMATIC]: {
        ambientIntensity: 0.5,
        directionalIntensity: 0.9,
        colorTemperature: 0.4,
        bloomStrength: 0.6,
        volumetricDensity: 0.3,
        shadowSoftness: 0.8
      },
      [LightingPreset.INTIMATE]: {
        ambientIntensity: 0.7,
        directionalIntensity: 0.3,
        colorTemperature: 0.6,
        bloomStrength: 0.4,
        volumetricDensity: 0.2,
        shadowSoftness: 0.9
      }
    };

    const config = presets[preset];
    if (config) {
      setState(prev => ({ ...prev, ...config }));
    }
  };

  // Update cursor light position
  const updateCursorLight = (x: number, y: number) => {
    setState(prev => ({
      ...prev,
      cursorLightX: x,
      cursorLightY: y
    }));
  };

  // Set overall lighting intensity
  const setIntensity = (intensity: number) => {
    setState(prev => ({
      ...prev,
      ambientIntensity: Math.max(0, Math.min(1, intensity)),
      directionalIntensity: Math.max(0, Math.min(1, intensity * 0.7))
    }));
  };

  // Trigger lighting pulse effect
  const triggerPulse = () => {
    setState(prev => ({ ...prev, pulsePhase: 0 }));
    
    if (pulseTimeoutRef.current) {
      clearTimeout(pulseTimeoutRef.current);
    }
    
    pulseTimeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, pulsePhase: Math.PI }));
    }, 1000);
  };

  // Generate CSS for lighting effects
  const getLightingCSS = (): React.CSSProperties => {
    const pulseIntensity = Math.sin(state.pulsePhase) * 0.1 + 1;
    const cursorGlowX = (state.cursorLightX - 0.5) * 100;
    const cursorGlowY = (state.cursorLightY - 0.5) * 100;
    
    return {
      // Ambient lighting overlay
      background: `radial-gradient(
        circle at ${state.cursorLightX * 100}% ${state.cursorLightY * 100}%,
        rgba(124, 58, 237, ${state.ambientIntensity * 0.3}) 0%,
        rgba(6, 182, 212, ${state.ambientIntensity * 0.2}) 30%,
        transparent 60%
      )`,
      
      // Bloom effect and color temperature
      filter: `
        brightness(${1 + state.bloomStrength * 0.3 * pulseIntensity})
        contrast(${1 + state.directionalIntensity * 0.1})
        hue-rotate(${state.colorTemperature * 30}deg) 
        saturate(${1 + state.bloomStrength * 0.5})
        ${state.volumetricDensity > 0.5 ? `blur(${state.volumetricDensity * 0.5}px)` : ''}
      `,
      
      // Dynamic shadow based on cursor
      boxShadow: `
        ${cursorGlowX}px ${cursorGlowY}px ${20 + state.shadowSoftness * 30}px rgba(124, 58, 237, ${state.volumetricDensity * 0.3}),
        inset 0 0 ${30 * pulseIntensity}px rgba(124, 58, 237, ${state.bloomStrength * 0.2})
      `
    };
  };

  return (
    <LightingContext.Provider value={{
      state,
      setPreset,
      updateCursorLight,
      setIntensity,
      triggerPulse,
      getLightingCSS
    }}>
      <motion.div
        className="lighting-engine"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: 1,
          ...getLightingCSS()
        }}
      >
        {/* Volumetric lighting layers */}
        <div
          className="volumetric-layer"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(
              ellipse at center,
              rgba(124, 58, 237, ${state.volumetricDensity * 0.2}) 0%,
              rgba(6, 182, 212, ${state.volumetricDensity * 0.1}) 40%,
              transparent 70%
            )`,
            mixBlendMode: 'screen',
            opacity: state.ambientIntensity
          }}
        />
        
        {/* Directional light source */}
        <div
          className="directional-light"
          style={{
            position: 'absolute',
            top: '20%',
            left: '30%',
            width: '400px',
            height: '400px',
            background: `radial-gradient(
              circle,
              rgba(124, 58, 237, ${state.directionalIntensity * 0.4}) 0%,
              transparent 50%
            )`,
            filter: `blur(${20 + state.shadowSoftness * 10}px)`,
            transform: `translate(${(state.cursorLightX - 0.5) * 50}px, ${(state.cursorLightY - 0.5) * 50}px)`,
            mixBlendMode: 'screen'
          }}
        />
        
        {/* Bloom layer */}
        <div
          className="bloom-layer"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(
              ellipse at ${state.cursorLightX * 100}% ${state.cursorLightY * 100}%,
              rgba(124, 58, 237, ${state.bloomStrength * 0.1}) 0%,
              transparent 50%
            )`,
            mixBlendMode: 'screen',
            opacity: Math.sin(state.pulsePhase) * 0.1 + 1
          }}
        />
      </motion.div>
      
      <div style={{ position: 'relative', zIndex: 2 }}>
        {children}
      </div>
    </LightingContext.Provider>
  );
};

// Hook for component-specific lighting
export const useComponentLighting = (intensity?: number) => {
  const { state, triggerPulse, getLightingCSS } = useLighting();
  
  const createGlowEffect = (customIntensity?: number) => ({
    style: {
      boxShadow: `
        0 0 ${20 * (customIntensity || intensity || state.ambientIntensity)}px rgba(124, 58, 237, 0.3),
        0 0 ${40 * (customIntensity || intensity || state.ambientIntensity)}px rgba(124, 58, 237, 0.1)
      `,
      filter: `brightness(${1 + state.bloomStrength * 0.2})`
    }
  });

  const createReactiveGlow = () => ({
    whileHover: {
      boxShadow: `
        0 0 ${30 * state.ambientIntensity}px rgba(124, 58, 237, 0.5),
        0 0 ${60 * state.ambientIntensity}px rgba(124, 58, 237, 0.2)
      `,
      transition: { duration: 0.3 }
    },
    onTap: () => triggerPulse()
  });

  return {
    state,
    triggerPulse,
    getLightingCSS,
    createGlowEffect,
    createReactiveGlow
  };
};
