import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

// Atmosphere state interface
export interface AtmosphereState {
  density: number;
  hazeIntensity: number;
  nebulaOpacity: number;
  gridVisibility: number;
  starfieldIntensity: number;
  particleCount: number;
  windStrength: number;
  temperature: number; // 0 = cold, 1 = warm
  depth: number;
  evolution: number; // Continuous evolution value
}

// Atmosphere presets for different environments
export enum AtmospherePreset {
  QUANTUM_VOID = 'quantum_void',
  NEBULA_FIELD = 'nebula_field',
  CYBER_SPACE = 'cyber_space',
  DEEP_SPACE = 'deep_space',
  ATMOSPHERIC_DREAM = 'atmospheric_dream'
}

// Context for global atmosphere management
const AtmosphereContext = createContext<{
  state: AtmosphereState;
  setPreset: (preset: AtmospherePreset) => void;
  updateDensity: (density: number) => void;
  evolveEnvironment: (progress: number) => void;
  getAtmosphereCSS: () => React.CSSProperties;
} | null>(null);

export const useAtmosphere = () => {
  const context = useContext(AtmosphereContext);
  if (!context) throw new Error('useAtmosphere must be used within AtmosphereProvider');
  return context;
};

interface AtmosphereProviderProps {
  children: React.ReactNode;
}

export const AtmosphereProvider: React.FC<AtmosphereProviderProps> = ({ children }) => {
  const animationFrameRef = useRef<number | undefined>(undefined);
  
  const [state, setState] = useState<AtmosphereState>({
    density: 0.5,
    hazeIntensity: 0.3,
    nebulaOpacity: 0.4,
    gridVisibility: 0.2,
    starfieldIntensity: 0.6,
    particleCount: 50,
    windStrength: 0.2,
    temperature: 0.3, // Cool
    depth: 0.7,
    evolution: 0
  });

  // Disable dynamic atmosphere for performance
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Atmosphere preset configurations
  const setPreset = (preset: AtmospherePreset) => {
    const presets = {
      [AtmospherePreset.QUANTUM_VOID]: {
        density: 0.2,
        hazeIntensity: 0.1,
        nebulaOpacity: 0.3,
        gridVisibility: 0.4,
        starfieldIntensity: 0.8,
        particleCount: 30,
        windStrength: 0.1,
        temperature: 0.1,
        depth: 1.0
      },
      [AtmospherePreset.NEBULA_FIELD]: {
        density: 0.7,
        hazeIntensity: 0.6,
        nebulaOpacity: 0.8,
        gridVisibility: 0.1,
        starfieldIntensity: 0.4,
        particleCount: 80,
        windStrength: 0.3,
        temperature: 0.5,
        depth: 0.6
      },
      [AtmospherePreset.CYBER_SPACE]: {
        density: 0.4,
        hazeIntensity: 0.2,
        nebulaOpacity: 0.2,
        gridVisibility: 0.7,
        starfieldIntensity: 0.5,
        particleCount: 60,
        windStrength: 0.4,
        temperature: 0.3,
        depth: 0.8
      },
      [AtmospherePreset.DEEP_SPACE]: {
        density: 0.1,
        hazeIntensity: 0.05,
        nebulaOpacity: 0.1,
        gridVisibility: 0.2,
        starfieldIntensity: 1.0,
        particleCount: 20,
        windStrength: 0.05,
        temperature: 0.0,
        depth: 1.0
      },
      [AtmospherePreset.ATMOSPHERIC_DREAM]: {
        density: 0.9,
        hazeIntensity: 0.8,
        nebulaOpacity: 0.9,
        gridVisibility: 0.05,
        starfieldIntensity: 0.3,
        particleCount: 120,
        windStrength: 0.2,
        temperature: 0.7,
        depth: 0.4
      }
    };

    const config = presets[preset];
    if (config) {
      setState(prev => ({ ...prev, ...config }));
    }
  };

  // Update atmosphere density
  const updateDensity = (density: number) => {
    setState(prev => ({
      ...prev,
      density: Math.max(0, Math.min(1, density))
    }));
  };

  // Evolve environment based on progress
  const evolveEnvironment = (progress: number) => {
    setState(prev => ({
      ...prev,
      evolution: progress,
      nebulaOpacity: prev.nebulaOpacity * (1 + progress * 0.2),
      starfieldIntensity: prev.starfieldIntensity * (1 - progress * 0.3)
    }));
  };

  // Generate CSS for atmospheric effects
  const getAtmosphereCSS = (): React.CSSProperties => {
    const windOffsetX = Math.sin(state.evolution * 2) * state.windStrength * 20;
    const windOffsetY = Math.cos(state.evolution * 1.5) * state.windStrength * 10;
    
    return {
      // Multi-layered atmospheric gradients
      background: `
        radial-gradient(
          ellipse at 30% 20%,
          rgba(124, 58, 237, ${state.nebulaOpacity * 0.3}) 0%,
          transparent 50%
        ),
        radial-gradient(
          ellipse at 70% 60%,
          rgba(6, 182, 212, ${state.nebulaOpacity * 0.2}) 0%,
          transparent 50%
        ),
        radial-gradient(
          ellipse at 20% 80%,
          rgba(139, 92, 246, ${state.nebulaOpacity * 0.15}) 0%,
          transparent 40%
        ),
        linear-gradient(
          180deg,
          rgba(11, 14, 20, ${1 - state.density * 0.3}) 0%,
          rgba(11, 14, 20, ${1 - state.density * 0.1}) 100%
        )
      `,
      
      // Atmospheric haze
      backdropFilter: `blur(${state.hazeIntensity * 2}px)`,
      
      // Wind effect
      transform: `translate(${windOffsetX}px, ${windOffsetY}px)`,
      
      // Depth perception
      perspective: `${1000 + state.depth * 2000}px`
    };
  };

  return (
    <AtmosphereContext.Provider value={{
      state,
      setPreset,
      updateDensity,
      evolveEnvironment,
      getAtmosphereCSS
    }}>
      <motion.div
        className="atmosphere-engine"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: 0,
          ...getAtmosphereCSS()
        }}
      >
        {/* Nebula layers */}
        <div
          className="nebula-layer-1"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(
              ellipse at 25% 25%,
              rgba(124, 58, 237, ${state.nebulaOpacity * 0.4}) 0%,
              rgba(139, 92, 246, ${state.nebulaOpacity * 0.2}) 30%,
              transparent 70%
            )`,
            mixBlendMode: 'screen',
            opacity: 0.8,
            transform: `scale(${1 + state.evolution * 0.1}) rotate(${state.evolution * 5}deg)`
          }}
        />
        
        <div
          className="nebula-layer-2"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(
              ellipse at 75% 75%,
              rgba(6, 182, 212, ${state.nebulaOpacity * 0.3}) 0%,
              rgba(34, 211, 238, ${state.nebulaOpacity * 0.15}) 40%,
              transparent 80%
            )`,
            mixBlendMode: 'screen',
            opacity: 0.6,
            transform: `scale(${1 - state.evolution * 0.05}) rotate(-${state.evolution * 3}deg)`
          }}
        />
        
        {/* Grid pattern */}
        <div
          className="atmospheric-grid"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `
              linear-gradient(rgba(255, 255, 255, ${state.gridVisibility * 0.02}) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255, 255, 255, ${state.gridVisibility * 0.02}) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
            opacity: state.gridVisibility,
            transform: `translate(${Math.sin(state.evolution * 2) * state.windStrength * 10}px, ${Math.cos(state.evolution * 1.5) * state.windStrength * 5}px)`
          }}
        />
        
        {/* Starfield */}
        <div
          className="starfield"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: state.starfieldIntensity
          }}
        >
          {Array.from({ length: Math.floor(state.particleCount * 0.3) }, (_, i) => (
            <div
              key={`star-${i}`}
              className="star"
              style={{
                position: 'absolute',
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                width: `${Math.random() * 2 + 0.5}px`,
                height: `${Math.random() * 2 + 0.5}px`,
                background: 'white',
                borderRadius: '50%',
                opacity: Math.random() * 0.8 + 0.2,
                animation: `twinkle ${Math.random() * 3 + 2}s infinite`,
                animationDelay: `${Math.random() * 3}s`
              }}
            />
          ))}
        </div>
        
        {/* Atmospheric haze */}
        <div
          className="atmospheric-haze"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `linear-gradient(
              180deg,
              rgba(124, 58, 237, ${state.hazeIntensity * 0.1}) 0%,
              transparent 30%,
              transparent 70%,
              rgba(6, 182, 212, ${state.hazeIntensity * 0.1}) 100%
            )`,
            filter: `blur(${state.hazeIntensity * 10}px)`,
            mixBlendMode: 'screen'
          }}
        />
      </motion.div>
      
      <div style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </div>
    </AtmosphereContext.Provider>
  );
};

// Hook for component-specific atmospheric effects
export const useComponentAtmosphere = (intensity?: number) => {
  const { state, evolveEnvironment } = useAtmosphere();
  
  const createAtmosphericGlow = (customIntensity?: number) => ({
    style: {
      filter: `
        blur(${state.hazeIntensity * (customIntensity || intensity || 1) * 3}px)
        brightness(${1 + state.nebulaOpacity * 0.2})
      `,
      mixBlendMode: 'screen' as const
    }
  });

  const createDepthEffect = (depth?: number) => ({
    style: {
      transform: `translateZ(${(depth || state.depth) * 100}px)`,
      opacity: 1 - (depth || state.depth) * 0.3,
      filter: `blur(${(depth || state.depth) * 2}px)`
    }
  });

  return {
    state,
    evolveEnvironment,
    createAtmosphericGlow,
    createDepthEffect
  };
};

// Add CSS animation for star twinkling
const style = document.createElement('style');
style.textContent = `
  @keyframes twinkle {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 1; }
  }
`;
document.head.appendChild(style);
