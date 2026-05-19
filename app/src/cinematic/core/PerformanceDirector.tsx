import React, { createContext, useContext, useEffect, useRef, useState } from 'react';

// Performance state interface
export interface PerformanceState {
  mode: 'high' | 'medium' | 'low';
  fps: number;
  frameTime: number;
  memoryUsage: number;
  gpuLoad: number;
  adaptiveQuality: number;
  particleLimit: number;
  effectIntensity: number;
  renderScale: number;
  isThrottling: boolean;
  lastOptimization: number;
}

// Performance thresholds
const PERFORMANCE_THRESHOLDS = {
  HIGH: { fps: 55, frameTime: 18, memory: 0.7, gpu: 0.8 },
  MEDIUM: { fps: 30, frameTime: 33, memory: 0.85, gpu: 0.9 },
  LOW: { fps: 15, frameTime: 66, memory: 0.95, gpu: 1.0 }
};

// Context for performance management
const PerformanceContext = createContext<{
  state: PerformanceState;
  setQualityMode: (mode: 'high' | 'medium' | 'low') => void;
  requestOptimization: () => void;
  getPerformanceMetrics: () => PerformanceState;
  shouldRenderComponent: (priority: 'high' | 'medium' | 'low') => boolean;
} | null>(null);

export const usePerformance = () => {
  const context = useContext(PerformanceContext);
  if (!context) throw new Error('usePerformance must be used within PerformanceProvider');
  return context;
};

interface PerformanceProviderProps {
  children: React.ReactNode;
}

export const PerformanceProvider: React.FC<PerformanceProviderProps> = ({ children }) => {
  const animationFrameRef = useRef<number | undefined>(undefined);
  const lastFrameTimeRef = useRef(performance.now());
  const frameCountRef = useRef(0);
  const fpsUpdateRef = useRef(0);
  
  const [state, setState] = useState<PerformanceState>({
    mode: 'high',
    fps: 60,
    frameTime: 16,
    memoryUsage: 0,
    gpuLoad: 0,
    adaptiveQuality: 1,
    particleLimit: 100,
    effectIntensity: 1,
    renderScale: 1,
    isThrottling: false,
    lastOptimization: Date.now()
  });

  // Performance monitoring system
  useEffect(() => {
    const monitorPerformance = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastFrameTimeRef.current;
      lastFrameTimeRef.current = currentTime;
      
      frameCountRef.current++;
      
      // Update FPS every 500ms
      if (currentTime - fpsUpdateRef.current > 500) {
        const fps = Math.round(frameCountRef.current * 1000 / (currentTime - fpsUpdateRef.current));
        const frameTime = Math.round(deltaTime);
        
        // Estimate memory usage (simplified)
        const memoryUsage = (performance as any).memory ? 
          (performance as any).memory.usedJSHeapSize / (performance as any).memory.jsHeapSizeLimit : 0;
        
        setState(prev => ({
          ...prev,
          fps,
          frameTime,
          memoryUsage: Math.min(1, memoryUsage)
        }));
        
        frameCountRef.current = 0;
        fpsUpdateRef.current = currentTime;
        
        // Auto-adjust quality based on performance
        adjustQuality(fps, frameTime, memoryUsage);
      }
      
      animationFrameRef.current = requestAnimationFrame(monitorPerformance);
    };

    monitorPerformance();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Quality adjustment based on performance metrics
  const adjustQuality = (fps: number, frameTime: number, memoryUsage: number) => {
    const currentTime = Date.now();
    
    // Don't adjust too frequently
    if (currentTime - state.lastOptimization < 2000) return;
    
    let newMode: 'high' | 'medium' | 'low' = state.mode;
    let shouldOptimize = false;
    
    // Determine performance mode based on thresholds
    if (fps < PERFORMANCE_THRESHOLDS.LOW.fps || 
        frameTime > PERFORMANCE_THRESHOLDS.LOW.frameTime ||
        memoryUsage > PERFORMANCE_THRESHOLDS.LOW.memory) {
      newMode = 'low';
      shouldOptimize = true;
    } else if (fps < PERFORMANCE_THRESHOLDS.MEDIUM.fps || 
               frameTime > PERFORMANCE_THRESHOLDS.MEDIUM.frameTime ||
               memoryUsage > PERFORMANCE_THRESHOLDS.MEDIUM.memory) {
      newMode = 'medium';
      shouldOptimize = true;
    } else if (fps > PERFORMANCE_THRESHOLDS.HIGH.fps && 
               frameTime < PERFORMANCE_THRESHOLDS.HIGH.frameTime &&
               memoryUsage < PERFORMANCE_THRESHOLDS.HIGH.memory &&
               state.mode !== 'high') {
      newMode = 'high';
      shouldOptimize = true;
    }
    
    if (shouldOptimize && newMode !== state.mode) {
      applyQualitySettings(newMode);
    }
  };

  // Apply quality settings based on mode
  const applyQualitySettings = (mode: 'high' | 'medium' | 'low') => {
    const settings = {
      high: {
        adaptiveQuality: 1,
        particleLimit: 100,
        effectIntensity: 1,
        renderScale: 1,
        isThrottling: false
      },
      medium: {
        adaptiveQuality: 0.7,
        particleLimit: 60,
        effectIntensity: 0.8,
        renderScale: 0.8,
        isThrottling: false
      },
      low: {
        adaptiveQuality: 0.4,
        particleLimit: 30,
        effectIntensity: 0.5,
        renderScale: 0.6,
        isThrottling: true
      }
    };
    
    const config = settings[mode];
    
    setState(prev => ({
      ...prev,
      mode,
      ...config,
      lastOptimization: Date.now()
    }));
    
    // Notify other systems of quality change
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('qualityChange', { 
        detail: { mode, ...config } 
      }));
    }
  };

  // Manual quality mode setting
  const setQualityMode = (mode: 'high' | 'medium' | 'low') => {
    if (mode !== state.mode) {
      applyQualitySettings(mode);
    }
  };

  // Request immediate optimization
  const requestOptimization = () => {
    // Force garbage collection if available
    if (typeof window !== 'undefined' && 'gc' in window) {
      (window as any).gc();
    }
    
    // Reduce quality temporarily
    const currentMode = state.mode;
    if (currentMode === 'high') {
      setQualityMode('medium');
      setTimeout(() => setQualityMode('high'), 3000);
    } else if (currentMode === 'medium') {
      setQualityMode('low');
      setTimeout(() => setQualityMode('medium'), 3000);
    }
  };

  // Get current performance metrics
  const getPerformanceMetrics = () => state;

  // Determine if component should render based on priority and performance
  const shouldRenderComponent = (priority: 'high' | 'medium' | 'low') => {
    switch (state.mode) {
      case 'high':
        return true;
      case 'medium':
        return priority === 'high' || priority === 'medium';
      case 'low':
        return priority === 'high';
      default:
        return true;
    }
  };

  // Mobile-specific optimizations
  useEffect(() => {
    const isMobile = window.innerWidth < 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile && state.mode === 'high') {
      setQualityMode('medium');
    }
  }, []);

  // Visibility-based performance adjustment
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Reduce performance when tab is not visible
        setState(prev => ({
          ...prev,
          adaptiveQuality: prev.adaptiveQuality * 0.5,
          isThrottling: true
        }));
      } else {
        // Restore performance when tab becomes visible
        applyQualitySettings(state.mode);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [state.mode]);

  return (
    <PerformanceContext.Provider value={{
      state,
      setQualityMode,
      requestOptimization,
      getPerformanceMetrics,
      shouldRenderComponent
    }}>
      {/* Performance overlay for development */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'fixed',
            top: 10,
            right: 10,
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            zIndex: 9999,
            pointerEvents: 'none'
          }}
        >
          <div>FPS: {state.fps}</div>
          <div>Mode: {state.mode}</div>
          <div>Quality: {Math.round(state.adaptiveQuality * 100)}%</div>
          <div>Particles: {state.particleLimit}</div>
          {state.isThrottling && <div style={{ color: 'orange' }}>THROTTLING</div>}
        </div>
      )}
      
      {children}
    </PerformanceContext.Provider>
  );
};

// Hook for component-specific performance optimization
export const useComponentPerformance = (priority: 'high' | 'medium' | 'low' = 'medium') => {
  const { state, shouldRenderComponent, requestOptimization } = usePerformance();
  
  const shouldRender = shouldRenderComponent(priority);
  
  const getOptimizedProps = () => ({
    particles: Math.floor(state.particleLimit * (priority === 'high' ? 1 : priority === 'medium' ? 0.6 : 0.3)),
    effects: state.effectIntensity * (priority === 'high' ? 1 : priority === 'medium' ? 0.7 : 0.4),
    quality: state.adaptiveQuality,
    scale: state.renderScale
  });
  
  const requestPerformanceBoost = () => {
    if (state.mode !== 'high') {
      requestOptimization();
    }
  };
  
  return {
    shouldRender,
    performanceMode: state.mode,
    getOptimizedProps,
    requestPerformanceBoost,
    isThrottling: state.isThrottling
  };
};

// Intersection observer for lazy loading performance optimization
export const usePerformanceIntersection = (threshold = 0.1) => {
  const [isVisible, setIsVisible] = useState(false);
  const { shouldRenderComponent } = usePerformance();
  const elementRef = useRef<HTMLElement>(null);
  
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold }
    );
    
    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold]);
  
  const shouldRender = isVisible && shouldRenderComponent('medium');
  
  return { elementRef, isVisible, shouldRender };
};
