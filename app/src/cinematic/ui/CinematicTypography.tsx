import React from 'react';
import { motion } from 'framer-motion';
import { useLighting } from '../core/LightingEngine';
import { useMotion } from '../core/MotionEngine';

// Typography variants for cinematic effects
export type TypographyVariant = 'massive' | 'large' | 'medium' | 'small' | 'micro';
export type GradientVariant = 'purple-to-cyan' | 'cyan-to-purple' | 'purple' | 'cyan' | 'white' | 'gold';

interface CinematicTypographyProps {
  tag?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span';
  text: string;
  variant?: TypographyVariant;
  gradient?: GradientVariant;
  animate?: any;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
  effect?: 'glitch' | 'wave' | 'pulse' | 'typewriter';
}

// Cinematic Typography Component
export const CinematicTypography: React.FC<CinematicTypographyProps> = ({
  tag: Tag = 'h1',
  text,
  variant = 'large',
  gradient = 'purple-to-cyan',
  animate,
  className = '',
  style = {},
  children,
  effect,
  ...props
}) => {
  const { state: lightingState } = useLighting();
  const { state: motionState } = useMotion();

  // Typography styles based on variant
  const variantStyles = {
    massive: {
      fontSize: 'clamp(3rem, 10vw, 8rem)',
      fontWeight: 900,
      lineHeight: 0.8,
      letterSpacing: '-0.03em',
      textTransform: 'uppercase' as const
    },
    large: {
      fontSize: 'clamp(2.5rem, 6vw, 5rem)',
      fontWeight: 800,
      lineHeight: 0.9,
      letterSpacing: '-0.02em',
      textTransform: 'uppercase' as const
    },
    medium: {
      fontSize: 'clamp(2rem, 4vw, 3rem)',
      fontWeight: 700,
      lineHeight: 1,
      letterSpacing: '-0.01em'
    },
    small: {
      fontSize: 'clamp(1.5rem, 3vw, 2rem)',
      fontWeight: 600,
      lineHeight: 1.1
    },
    micro: {
      fontSize: 'clamp(1rem, 2vw, 1.5rem)',
      fontWeight: 500,
      lineHeight: 1.2
    }
  };

  // Gradient styles
  const gradientStyles = {
    'purple-to-cyan': {
      background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      filter: `drop-shadow(0 0 ${30 * lightingState.bloomStrength}px rgba(124, 58, 237, 0.5))`
    },
    'cyan-to-purple': {
      background: 'linear-gradient(135deg, #06B6D4, #7C3AED)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      filter: `drop-shadow(0 0 ${30 * lightingState.bloomStrength}px rgba(6, 182, 212, 0.5))`
    },
    'purple': {
      color: '#7C3AED',
      textShadow: `0 0 ${20 * lightingState.bloomStrength}px rgba(124, 58, 237, 0.8)`
    },
    'cyan': {
      color: '#06B6D4',
      textShadow: `0 0 ${20 * lightingState.bloomStrength}px rgba(6, 182, 212, 0.8)`
    },
    'white': {
      color: '#FFFFFF',
      textShadow: `0 0 ${15 * lightingState.bloomStrength}px rgba(255, 255, 255, 0.5)`
    },
    'gold': {
      background: 'linear-gradient(135deg, #FFD700, #FFA500)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      filter: `drop-shadow(0 0 ${25 * lightingState.bloomStrength}px rgba(255, 215, 0, 0.6))`
    }
  };

  // Base styles
  const baseStyles = {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    margin: 0,
    ...variantStyles[variant],
    ...gradientStyles[gradient],
    ...style
  };

  // Animation presets
  const animationPresets = {
    glitch: {
      animate: {
        textShadow: [
          `0 0 ${10 * lightingState.bloomStrength}px rgba(124, 58, 237, 0.8)`,
          `0 0 ${20 * lightingState.bloomStrength}px rgba(6, 182, 212, 0.8)`,
          `0 0 ${10 * lightingState.bloomStrength}px rgba(255, 0, 255, 0.8)`,
          `0 0 ${10 * lightingState.bloomStrength}px rgba(124, 58, 237, 0.8)`
        ],
        x: [0, -2, 2, 0],
        y: [0, 1, -1, 0]
      },
      transition: {
        duration: 0.3,
        repeat: Infinity,
        repeatDelay: 3
      }
    },
    wave: {
      animate: {
        y: [-5, 5, -5],
        rotateY: [0, 5, 0, -5, 0]
      },
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut"
      }
    },
    pulse: {
      animate: {
        scale: [1, 1.05, 1],
        opacity: [0.8, 1, 0.8]
      },
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    },
    typewriter: {
      initial: { width: 0 },
      animate: { width: '100%' },
      transition: {
        duration: text.length * 0.05,
        ease: "easeOut"
      },
      style: {
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        borderRight: `2px solid ${gradient === 'purple-to-cyan' ? '#7C3AED' : '#06B6D4'}`
      }
    }
  };

  // Motion-based effects
  const motionEffects = {
    velocityReaction: {
      animate: {
        x: motionState.globalVelocity.x * motionState.intensity * 0.5,
        y: motionState.globalVelocity.y * motionState.intensity * 0.5,
        scale: 1 + (motionState.scrollVelocity * 0.005)
      },
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 20
      }
    }
  };

  // Get motion tag
  const MotionTag = motion[Tag as keyof typeof motion] as any;

  // Combine animations
  const combinedAnimate = effect ? 
    { ...animationPresets[effect], ...animate } : 
    { ...motionEffects.velocityReaction, ...animate };

  return (
    <MotionTag
      className={`cinematic-typography ${className}`}
      style={baseStyles}
      animate={combinedAnimate}
      {...props}
    >
      {text}
      {children}
    </MotionTag>
  );
};

// Specialized typography components
export const HeroTitle: React.FC<{ text: string; delay?: number }> = ({ text, delay = 0 }) => (
  <CinematicTypography
    tag="h1"
    text={text}
    variant="massive"
    gradient="purple-to-cyan"
    animate={{
      initial: { opacity: 0, y: 100, scale: 0.8 },
      animate: { opacity: 1, y: 0, scale: 1 },
      transition: { duration: 1.5, ease: "easeOut", delay }
    }}
  />
);

export const SectionTitle: React.FC<{ text: string; delay?: number }> = ({ text, delay = 0 }) => (
  <CinematicTypography
    tag="h2"
    text={text}
    variant="large"
    gradient="cyan-to-purple"
    animate={{
      initial: { opacity: 0, y: 50 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 1.2, ease: "easeOut", delay }
    }}
  />
);

export const GlitchText: React.FC<{ text: string; variant?: TypographyVariant }> = ({ text, variant = 'medium' }) => (
  <CinematicTypography
    tag="h3"
    text={text}
    variant={variant}
    gradient="purple"
    effect="glitch"
  />
);

export const WaveText: React.FC<{ text: string; variant?: TypographyVariant }> = ({ text, variant = 'medium' }) => (
  <CinematicTypography
    tag="p"
    text={text}
    variant={variant}
    gradient="cyan"
    effect="wave"
  />
);

export const TypewriterText: React.FC<{ text: string; variant?: TypographyVariant }> = ({ text, variant = 'small' }) => (
  <CinematicTypography
    tag="span"
    text={text}
    variant={variant}
    gradient="white"
    effect="typewriter"
  />
);

// Hook for typography animations
export const useTypographyAnimation = () => {
  const { state: lightingState } = useLighting();
  const { state: motionState } = useMotion();

  const createRevealAnimation = (delay?: number) => ({
    initial: { opacity: 0, y: 30 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8, ease: "easeOut", delay: delay || 0 }
  });

  const createScrollAnimation = () => ({
    initial: { opacity: 0, x: -50 },
    whileInView: { opacity: 1, x: 0 },
    viewport: { once: true, margin: "-100px" },
    transition: { duration: 0.6, ease: "easeOut" }
  });

  const createStaggerAnimation = (staggerDelay?: number) => ({
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    transition: { 
      duration: 0.6, 
      ease: "easeOut",
      staggerChildren: staggerDelay || 0.1
    }
  });

  return {
    createRevealAnimation,
    createScrollAnimation,
    createStaggerAnimation,
    lightingIntensity: lightingState.bloomStrength,
    motionIntensity: motionState.intensity
  };
};
