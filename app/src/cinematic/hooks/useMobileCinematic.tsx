import { useState, useEffect } from 'react';
import { usePerformance } from '../core/PerformanceDirector';
import { useMotion } from '../core/MotionEngine';
import { useLighting } from '../core/LightingEngine';
import { useAtmosphere } from '../core/AtmosphereEngine';

// Mobile cinematic experience hook with visual silence
export const useMobileCinematic = () => {
  const { setQualityMode } = usePerformance();
  const { setIntensity } = useMotion();
  const { setPreset, setIntensity: setLightingIntensity } = useLighting();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  
  const [isMobile, setIsMobile] = useState(false);
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [isLowPowerMode, setIsLowPowerMode] = useState(false);

  // Detect mobile device and capabilities
  useEffect(() => {
    const detectMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const isMobileDevice = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      const isSmallScreen = window.innerWidth <= 768;
      
      setIsMobile(isMobileDevice || (isTouchDevice && isSmallScreen));
    };

    detectMobile();
    window.addEventListener('resize', detectMobile);
    
    return () => window.removeEventListener('resize', detectMobile);
  }, []);

  // Detect reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);
    
    const handleChange = (e: MediaQueryListEvent) => setIsReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);
    
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Monitor battery level
  useEffect(() => {
    const getBatteryInfo = async () => {
      if ('getBattery' in navigator) {
        try {
          const battery = await (navigator as any).getBattery();
          setBatteryLevel(battery.level * 100);
          setIsLowPowerMode(battery.level < 0.2 || battery.charging === false);
          
          battery.addEventListener('levelchange', () => {
            setBatteryLevel(battery.level * 100);
            setIsLowPowerMode(battery.level < 0.2 || battery.charging === false);
          });
          
          battery.addEventListener('chargingchange', () => {
            setIsLowPowerMode(battery.level < 0.2 || battery.charging === false);
          });
        } catch (error) {
          // Battery API not available or permission denied
          console.log('Battery API not available');
        }
      }
    };

    getBatteryInfo();
  }, []);

  // Apply mobile optimizations
  useEffect(() => {
    if (isMobile || isReducedMotion || isLowPowerMode) {
      // Set performance mode to low for mobile/battery saving
      setQualityMode('low');
      
      // Reduce motion intensity
      setIntensity(0.3);
      
      // Set atmospheric presets for visual silence
      setAtmospherePreset('atmospheric_dream' as any);
      setPreset('atmospheric' as any);
      setLightingIntensity(0.4);
      
      // Disable complex animations
      if (isReducedMotion) {
        document.body.style.setProperty('--motion-scale', '0');
        document.body.classList.add('reduced-motion');
      }
      
      // Apply mobile-specific styles
      if (isMobile) {
        document.body.classList.add('mobile-cinematic');
      }
      
      // Apply low power mode styles
      if (isLowPowerMode) {
        document.body.classList.add('low-power-mode');
      }
    } else {
      // Restore full cinematic experience
      setQualityMode('high');
      setIntensity(1);
      setPreset('cinematic' as any);
      setLightingIntensity(1);
      
      document.body.classList.remove('reduced-motion', 'mobile-cinematic', 'low-power-mode');
      document.body.style.removeProperty('--motion-scale');
    }
  }, [isMobile, isReducedMotion, isLowPowerMode, setQualityMode, setIntensity, setPreset, setLightingIntensity, setAtmospherePreset]);

  // Visual silence configuration
  const getVisualSilenceConfig = () => {
    return {
      particleCount: isMobile ? 15 : isLowPowerMode ? 8 : 50,
      animationDuration: isReducedMotion ? 0 : isMobile ? 4 : 8,
      blurIntensity: isMobile ? 0.5 : isLowPowerMode ? 0.3 : 1,
      glowIntensity: isMobile ? 0.6 : isLowPowerMode ? 0.4 : 1,
      motionScale: isReducedMotion ? 0 : isMobile ? 0.5 : 1,
      transitionDuration: isReducedMotion ? 0.1 : isMobile ? 0.3 : 0.6
    };
  };

  // Mobile-specific animation presets
  const getMobileAnimationPreset = (preset: string) => {
    const config = getVisualSilenceConfig();
    
    switch (preset) {
      case 'subtle':
        return {
          duration: config.transitionDuration,
          ease: "easeOut",
          scale: 1,
          opacity: 0.8
        };
      
      case 'gentle':
        return {
          duration: config.transitionDuration * 1.5,
          ease: "easeInOut",
          scale: 1.02,
          opacity: 0.9
        };
      
      case 'minimal':
        return {
          duration: config.transitionDuration * 0.5,
          ease: "linear",
          scale: 1,
          opacity: 1
        };
      
      default:
        return {
          duration: config.transitionDuration,
          ease: "easeOut",
          scale: 1,
          opacity: 0.8
        };
    }
  };

  // Touch-optimized interactions
  const getTouchOptimizedProps = () => {
    if (!isMobile) return {};
    
    return {
      whileTap: {
        scale: 0.98,
        transition: { duration: 0.1 }
      },
      style: {
        cursor: 'pointer',
        WebkitTapHighlightColor: 'transparent',
        touchAction: 'manipulation'
      }
    };
  };

  // Battery-aware performance
  const getBatteryAwarePerformance = () => {
    if (!batteryLevel) return { particles: 30, effects: 1, quality: 'high' as const };
    
    if (batteryLevel < 20) {
      return { particles: 8, effects: 0.3, quality: 'low' as const };
    } else if (batteryLevel < 50) {
      return { particles: 20, effects: 0.6, quality: 'medium' as const };
    } else {
      return { particles: 50, effects: 1, quality: 'high' as const };
    }
  };

  return {
    isMobile,
    isReducedMotion,
    isLowPowerMode,
    batteryLevel,
    visualSilenceConfig: getVisualSilenceConfig(),
    getMobileAnimationPreset,
    getTouchOptimizedProps,
    getBatteryAwarePerformance
  };
};

// Mobile-specific CSS classes
export const mobileCinematicStyles = `
  .mobile-cinematic {
    --particle-count: 15;
    --animation-duration: 4s;
    --blur-intensity: 0.5;
    --glow-intensity: 0.6;
    --motion-scale: 0.5;
  }

  .reduced-motion {
    --particle-count: 0;
    --animation-duration: 0s;
    --blur-intensity: 0;
    --glow-intensity: 0.3;
    --motion-scale: 0;
  }

  .reduced-motion * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .low-power-mode {
    --particle-count: 8;
    --animation-duration: 6s;
    --blur-intensity: 0.3;
    --glow-intensity: 0.4;
    --motion-scale: 0.3;
  }

  .mobile-cinematic .cinematic-orb {
    transform: scale(0.7);
  }

  .mobile-cinematic .particle-field {
    opacity: 0.6;
  }

  .mobile-cinematic .energy-connections {
    opacity: 0.4;
  }

  .mobile-cinematic .glow-effect {
    filter: brightness(0.8) blur(2px);
  }

  @media (max-width: 768px) {
    .mobile-cinematic {
      --particle-count: 10;
      --animation-duration: 3s;
    }
  }

  @media (max-width: 480px) {
    .mobile-cinematic {
      --particle-count: 5;
      --animation-duration: 2s;
      --glow-intensity: 0.4;
    }
  }
`;

// Hook for mobile-specific UI components
export const useMobileUI = () => {
  const { isMobile, getTouchOptimizedProps } = useMobileCinematic();
  
  const getMobileButtonProps = () => {
    if (!isMobile) return {};
    
    return {
      ...getTouchOptimizedProps(),
      style: {
        minHeight: '48px',
        minWidth: '48px',
        padding: '12px 24px',
        fontSize: '16px',
        ...getTouchOptimizedProps().style
      }
    };
  };

  const getMobileTypographyProps = () => {
    if (!isMobile) return {};
    
    return {
      style: {
        fontSize: 'clamp(1rem, 4vw, 1.5rem)',
        lineHeight: 1.4,
        letterSpacing: '0.01em'
      }
    };
  };

  return {
    getMobileButtonProps,
    getMobileTypographyProps
  };
};
