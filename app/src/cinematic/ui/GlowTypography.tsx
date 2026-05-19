import React from 'react';
import { motion } from 'framer-motion';
import { useLighting } from '../core/LightingEngine';

interface GlowTypographyProps {
  tag?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span';
  text: string;
  variant?: 'massive' | 'large' | 'medium' | 'small';
  gradient?: 'purple-to-cyan' | 'cyan-to-purple' | 'purple' | 'cyan' | 'white';
  animate?: any;
  className?: string;
  style?: React.CSSProperties;
}

export const GlowTypography: React.FC<GlowTypographyProps> = ({
  tag: Tag = 'h1',
  text,
  variant = 'large',
  gradient = 'purple-to-cyan',
  animate,
  className = '',
  style = {},
  ...props
}) => {
  const { state: lightingState } = useLighting();

  const variantStyles = {
    massive: {
      fontSize: 'clamp(3rem, 8vw, 6rem)',
      fontWeight: 800,
      lineHeight: 0.9,
      letterSpacing: '-0.02em'
    },
    large: {
      fontSize: 'clamp(2rem, 5vw, 4rem)',
      fontWeight: 700,
      lineHeight: 1,
      letterSpacing: '-0.01em'
    },
    medium: {
      fontSize: 'clamp(1.5rem, 3vw, 2.5rem)',
      fontWeight: 600,
      lineHeight: 1.1
    },
    small: {
      fontSize: 'clamp(1rem, 2vw, 1.5rem)',
      fontWeight: 500,
      lineHeight: 1.2
    }
  };

  const gradientStyles = {
    'purple-to-cyan': {
      background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    },
    'cyan-to-purple': {
      background: 'linear-gradient(135deg, #06B6D4, #7C3AED)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    },
    'purple': {
      color: '#7C3AED',
      textShadow: `0 0 ${20 * lightingState.bloomStrength}px rgba(124, 58, 237, 0.5)`
    },
    'cyan': {
      color: '#06B6D4',
      textShadow: `0 0 ${20 * lightingState.bloomStrength}px rgba(6, 182, 212, 0.5)`
    },
    'white': {
      color: '#FFFFFF',
      textShadow: `0 0 ${15 * lightingState.bloomStrength}px rgba(255, 255, 255, 0.3)`
    }
  };

  const baseStyles = {
    fontFamily: 'Urbanist, sans-serif',
    margin: 0,
    ...variantStyles[variant],
    ...gradientStyles[gradient],
    ...style
  };

  const MotionTag = motion[Tag as keyof typeof motion] as any;

  return (
    <MotionTag
      className={`glow-typography ${className}`}
      style={baseStyles}
      animate={animate}
      {...props}
    >
      {text}
    </MotionTag>
  );
};
