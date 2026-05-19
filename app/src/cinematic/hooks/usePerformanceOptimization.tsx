import { useRef, useCallback, useEffect } from 'react';

// Performance optimization hook for throttling and debouncing
export const usePerformanceOptimization = () => {
  const lastUpdateRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);
  const pendingUpdatesRef = useRef<Map<string, any>>(new Map());

  // Throttled update function
  const throttle = useCallback((fn: () => void, delay: number = 16) => {
    const now = performance.now();
    if (now - lastUpdateRef.current >= delay) {
      lastUpdateRef.current = now;
      fn();
    } else {
      // Schedule for next frame if not already scheduled
      if (!animationFrameRef.current) {
        animationFrameRef.current = requestAnimationFrame(() => {
          fn();
          animationFrameRef.current = null;
        });
      }
    }
  }, []);

  // Debounced update function
  const debounce = useCallback((fn: () => void, delay: number = 100) => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    animationFrameRef.current = requestAnimationFrame(() => {
      setTimeout(fn, delay);
      animationFrameRef.current = null;
    });
  }, []);

  // Batch multiple updates together
  const batchUpdate = useCallback((key: string, value: any, updateFn: (updates: Map<string, any>) => void) => {
    pendingUpdatesRef.current.set(key, value);
    
    if (!animationFrameRef.current) {
      animationFrameRef.current = requestAnimationFrame(() => {
        updateFn(pendingUpdatesRef.current);
        pendingUpdatesRef.current.clear();
        animationFrameRef.current = null;
      });
    }
  }, []);

  // Cleanup function
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return {
    throttle,
    debounce,
    batchUpdate
  };
};

// FPS monitoring hook
export const useFPSMonitor = () => {
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const fpsRef = useRef(60);

  const getFPS = useCallback(() => {
    frameCountRef.current++;
    const now = performance.now();
    const delta = now - lastTimeRef.current;
    
    if (delta >= 1000) {
      fpsRef.current = Math.round((frameCountRef.current * 1000) / delta);
      frameCountRef.current = 0;
      lastTimeRef.current = now;
    }
    
    return fpsRef.current;
  }, []);

  return { getFPS, currentFPS: fpsRef.current };
};

// Memory monitoring hook
export const useMemoryMonitor = () => {
  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: Math.round(memory.usedJSHeapSize / 1048576), // MB
        total: Math.round(memory.totalJSHeapSize / 1048576), // MB
        limit: Math.round(memory.jsHeapSizeLimit / 1048576) // MB
      };
    }
    return null;
  }, []);

  return { getMemoryUsage };
};
