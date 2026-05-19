import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import gsap from 'gsap';

// Register GSAP plugin
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// Experience state types
export interface ExperienceState {
  currentScene: number;
  scrollProgress: number;
  scrollVelocity: number;
  isScrolling: boolean;
  lightingIntensity: number;
  atmosphereDensity: number;
  cameraPosition: { x: number; y: number; z: number };
  isTransitioning: boolean;
  performanceMode: 'high' | 'medium' | 'low';
}

// Scene progression states
export enum SceneState {
  ARRIVAL = 'arrival',
  AWAKENING = 'awakening',
  QUANTUM = 'quantum',
  OPERATING_SYSTEM = 'operating_system',
  TRUST = 'trust',
  FINALE = 'finale'
}

// Context for global experience management
const ExperienceContext = createContext<{
  state: ExperienceState;
  updateScene: (scene: number) => void;
  updateLighting: (intensity: number) => void;
  updateAtmosphere: (density: number) => void;
  updateCamera: (position: Partial<{ x: number; y: number; z: number }>) => void;
  setTransitioning: (isTransitioning: boolean) => void;
} | null>(null);

export const useExperience = () => {
  const context = useContext(ExperienceContext);
  if (!context) throw new Error('useExperience must be used within ExperienceProvider');
  return context;
};

interface ExperienceProviderProps {
  children: React.ReactNode;
}

export const ExperienceProvider: React.FC<ExperienceProviderProps> = ({ children }) => {
  const animationFrameRef = useRef<number | undefined>(undefined);
  
  const [state, setState] = useState<ExperienceState>({
    currentScene: 0,
    scrollProgress: 0,
    scrollVelocity: 0,
    isScrolling: false,
    lightingIntensity: 0.7,
    atmosphereDensity: 0.5,
    cameraPosition: { x: 0, y: 0, z: 0 },
    isTransitioning: false,
    performanceMode: 'high'
  });

  // Detect performance mode
  useEffect(() => {
    const detectPerformance = () => {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl');
      const renderer = gl?.getParameter(gl.RENDERER);
      
      let mode: 'high' | 'medium' | 'low' = 'high';
      
      // Simple performance detection based on device and capabilities
      if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        mode = 'low';
      } else if (window.innerWidth < 768) {
        mode = 'medium';
      } else if (renderer && (renderer.includes('Intel') || renderer.includes('Mali'))) {
        mode = 'medium';
      }
      
      setState(prev => ({ ...prev, performanceMode: mode }));
    };

    detectPerformance();
    window.addEventListener('resize', detectPerformance);
    return () => window.removeEventListener('resize', detectPerformance);
  }, []);

  // Initialize Lenis smooth scrolling with aggressive optimization
  useEffect(() => {
    // Disable all animation loops for performance
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Scene progression logic
  const updateScene = (scene: number) => {
    setState(prev => ({ ...prev, currentScene: scene, isTransitioning: true }));
    
    // Auto-clear transition state
    setTimeout(() => {
      setState(prev => ({ ...prev, isTransitioning: false }));
    }, 1000);
  };

  // Lighting intensity control
  const updateLighting = (intensity: number) => {
    setState(prev => ({ ...prev, lightingIntensity: Math.max(0, Math.min(1, intensity)) }));
  };

  // Atmosphere density control
  const updateAtmosphere = (density: number) => {
    setState(prev => ({ ...prev, atmosphereDensity: Math.max(0, Math.min(1, density)) }));
  };

  // Camera position updates
  const updateCamera = (position: Partial<{ x: number; y: number; z: number }>) => {
    setState(prev => ({
      ...prev,
      cameraPosition: { ...prev.cameraPosition, ...position }
    }));
  };

  // Transition state control
  const setTransitioning = (isTransitioning: boolean) => {
    setState(prev => ({ ...prev, isTransitioning }));
  };

  // Environmental continuity - elements evolve between scenes
  useEffect(() => {
    const sceneProgress = state.scrollProgress;
    
    // Update lighting based on scene progression
    const lightingIntensity = 0.7 + (sceneProgress * 0.3);
    updateLighting(lightingIntensity);
    
    // Update atmosphere density
    const atmosphereDensity = 0.5 + (Math.sin(sceneProgress * Math.PI) * 0.3);
    updateAtmosphere(atmosphereDensity);
    
    // Update camera position for subtle drift
    const cameraX = Math.sin(sceneProgress * Math.PI * 2) * 10;
    const cameraY = Math.cos(sceneProgress * Math.PI) * 5;
    updateCamera({ x: cameraX, y: cameraY });
    
    // Scene progression based on scroll
    const sceneThresholds = [0, 0.15, 0.35, 0.55, 0.75, 0.9];
    const newScene = sceneThresholds.findIndex((threshold, index) => 
      sceneProgress >= threshold && (index === sceneThresholds.length - 1 || sceneProgress < sceneThresholds[index + 1])
    );
    
    if (newScene !== state.currentScene && newScene >= 0) {
      updateScene(newScene);
    }
  }, [state.scrollProgress]);

  return (
    <ExperienceContext.Provider value={{
      state,
      updateScene,
      updateLighting,
      updateAtmosphere,
      updateCamera,
      setTransitioning
    }}>
      <motion.div
        className="cinematic-experience"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2, ease: "easeInOut" }}
      >
        {children}
      </motion.div>
    </ExperienceContext.Provider>
  );
};

// Hook for scene-specific logic
export const useSceneState = (sceneName: SceneState) => {
  const { state } = useExperience();
  const sceneIndex = Object.values(SceneState).indexOf(sceneName);
  
  return {
    isActive: state.currentScene === sceneIndex,
    isTransitioning: state.isTransitioning,
    progress: state.scrollProgress,
    velocity: state.scrollVelocity,
    lighting: state.lightingIntensity,
    atmosphere: state.atmosphereDensity,
    camera: state.cameraPosition,
    performance: state.performanceMode
  };
};
