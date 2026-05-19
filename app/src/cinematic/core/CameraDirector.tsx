import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

// Camera state interface
export interface CameraState {
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  zoom: number;
  focus: { x: number; y: number; z: number };
  depthOfField: number;
  isMoving: boolean;
}

// Camera behavior presets
export enum CameraPreset {
  HERO = 'hero',
  INTIMATE = 'intimate',
  CINEMATIC = 'cinematic',
  TECHNICAL = 'technical',
  ATMOSPHERIC = 'atmospheric'
}

// Context for camera management
const CameraContext = React.createContext<{
  state: CameraState;
  setPreset: (preset: CameraPreset) => void;
  moveTo: (position: Partial<CameraState>) => void;
  focusOn: (point: { x: number; y: number; z: number }) => void;
  setDepth: (depth: number) => void;
} | null>(null);

export const useCamera = () => {
  const context = React.useContext(CameraContext);
  if (!context) throw new Error('useCamera must be used within CameraProvider');
  return context;
};

interface CameraProviderProps {
  children: React.ReactNode;
}

export const CameraProvider: React.FC<CameraProviderProps> = ({ children }) => {
    const animationFrameRef = useRef<number | undefined>(undefined);
  
  const [state, setState] = useState<CameraState>({
    position: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0, z: 0 },
    zoom: 1,
    focus: { x: 0, y: 0, z: 0 },
    depthOfField: 0,
    isMoving: false
  });

  // Disable dynamic camera for performance
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Camera preset configurations
  const setPreset = (preset: CameraPreset) => {
    const presets = {
      [CameraPreset.HERO]: {
        position: { x: 0, y: 0, z: 0 },
        rotation: { x: 0, y: 0, z: 0 },
        zoom: 1,
        depthOfField: 0
      },
      [CameraPreset.INTIMATE]: {
        position: { x: 0, y: -20, z: 50 },
        rotation: { x: 0.1, y: 0, z: 0 },
        zoom: 1.3,
        depthOfField: 0.3
      },
      [CameraPreset.CINEMATIC]: {
        position: { x: -30, y: -15, z: 100 },
        rotation: { x: 0.05, y: 0.2, z: 0 },
        zoom: 0.8,
        depthOfField: 0.5
      },
      [CameraPreset.TECHNICAL]: {
        position: { x: 0, y: 0, z: 80 },
        rotation: { x: 0, y: 0, z: 0 },
        zoom: 1.1,
        depthOfField: 0.1
      },
      [CameraPreset.ATMOSPHERIC]: {
        position: { x: 20, y: 10, z: 150 },
        rotation: { x: -0.05, y: -0.1, z: 0 },
        zoom: 0.7,
        depthOfField: 0.8
      }
    };

    const config = presets[preset];
    if (config) {
      setState(prev => ({ ...prev, ...config }));
    }
  };

  // Move camera to specific position
  const moveTo = (position: Partial<CameraState>) => {
    setState(prev => ({ ...prev, ...position, isMoving: true }));
    
    // Auto-clear moving state
    setTimeout(() => {
      setState(prev => ({ ...prev, isMoving: false }));
    }, 1000);
  };

  // Focus camera on specific point
  const focusOn = (point: { x: number; y: number; z: number }) => {
    setState(prev => ({
      ...prev,
      focus: point,
      isMoving: true
    }));
    
    setTimeout(() => {
      setState(prev => ({ ...prev, isMoving: false }));
    }, 800);
  };

  // Set depth of field
  const setDepth = (depth: number) => {
    setState(prev => ({
      ...prev,
      depthOfField: Math.max(0, Math.min(1, depth))
    }));
  };

  // Generate CSS transform for camera
  const getCameraTransform = () => {
    const { position, rotation, zoom } = state;
    return `
      translate3d(${position.x}px, ${position.y}px, ${position.z}px)
      rotateX(${rotation.x}rad)
      rotateY(${rotation.y}rad)
      rotateZ(${rotation.z}rad)
      scale(${zoom})
    `;
  };

  
  return (
    <CameraContext.Provider value={{
      state,
      setPreset,
      moveTo,
      focusOn,
      setDepth
    }}>
      <motion.div
        className="cinematic-camera"
        style={{
          transform: getCameraTransform(),
          transition: state.isMoving ? 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)' : 'none'
        }}
      >
        <div 
          className="camera-depth-field"
          style={{
            perspective: '1000px',
            perspectiveOrigin: '50% 50%'
          }}
        >
          {children}
        </div>
      </motion.div>
    </CameraContext.Provider>
  );
};

// Hook for scene-specific camera behavior
export const useSceneCamera = (sceneName: string) => {
  const { state, setPreset, moveTo, focusOn } = useCamera();
  
  const applySceneBehavior = () => {
    switch (sceneName) {
      case 'arrival':
        setPreset(CameraPreset.HERO);
        break;
      case 'awakening':
        setPreset(CameraPreset.INTIMATE);
        moveTo({ position: { x: 10, y: -5, z: 30 } });
        break;
      case 'quantum':
        setPreset(CameraPreset.TECHNICAL);
        break;
      case 'operating_system':
        setPreset(CameraPreset.CINEMATIC);
        break;
      case 'trust':
        setPreset(CameraPreset.ATMOSPHERIC);
        break;
      case 'finale':
        setPreset(CameraPreset.HERO);
        moveTo({ position: { x: 0, y: 0, z: 0 } });
        break;
      default:
        setPreset(CameraPreset.HERO);
    }
  };

  return {
    state,
    applySceneBehavior,
    moveTo,
    focusOn,
    setPreset
  };
};
