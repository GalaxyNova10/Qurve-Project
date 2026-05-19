import React from 'react';
import { motion } from 'framer-motion';
import { useLighting } from '../core/LightingEngine';
import { useMotion } from '../core/MotionEngine';

interface CinematicButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  type?: 'button' | 'submit' | 'reset';
}

export const CinematicButton: React.FC<CinematicButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  onClick,
  disabled = false,
  className = '',
  style = {},
  ...motionProps
}) => {
  const { createGlowEffect } = useLighting();
  const { getSpringConfig } = useMotion();

  const baseStyles = {
    position: 'relative' as const,
    border: 'none',
    borderRadius: '0.75rem',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontFamily: 'Urbanist, sans-serif',
    fontWeight: 600,
    letterSpacing: '0.025em',
    textTransform: 'uppercase' as const,
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    ...style
  };

  const variantStyles = {
    primary: {
      background: 'linear-gradient(135deg, #7C3AED, #6D28D9)',
      color: '#FFFFFF',
      boxShadow: '0 0 20px rgba(124, 58, 237, 0.3), 0 0 40px rgba(124, 58, 237, 0.1)',
      ...createGlowEffect()
    },
    secondary: {
      background: 'transparent',
      color: '#FFFFFF',
      border: '1px solid rgba(124, 58, 237, 0.5)',
      boxShadow: '0 0 10px rgba(124, 58, 237, 0.1)'
    }
  };

  const sizeStyles = {
    small: {
      padding: '0.5rem 1rem',
      fontSize: '0.875rem'
    },
    medium: {
      padding: '0.75rem 1.5rem',
      fontSize: '1rem'
    },
    large: {
      padding: '1rem 2rem',
      fontSize: '1.125rem'
    }
  };

  return (
    <motion.button
      className={`cinematic-button ${className}`}
      disabled={disabled}
      onClick={onClick}
      style={{
        ...baseStyles,
        ...variantStyles[variant],
        ...sizeStyles[size]
      }}
      whileHover={!disabled ? {
        scale: 1.05,
        boxShadow: variant === 'primary' 
          ? '0 0 30px rgba(124, 58, 237, 0.5), 0 0 60px rgba(124, 58, 237, 0.2)'
          : '0 0 20px rgba(124, 58, 237, 0.3), 0 0 40px rgba(124, 58, 237, 0.1)',
        transition: { ...getSpringConfig() }
      } : {}}
      whileTap={!disabled ? {
        scale: 0.98,
        transition: { duration: 0.1 }
      } : {}}
      {...motionProps}
    >
      {/* Animated background gradient for primary variant */}
      {variant === 'primary' && (
        <motion.div
          className="button-gradient"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
            transform: 'translateX(-100%)'
          }}
          animate={{
            transform: ['translateX(-100%)', 'translateX(100%)']
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "linear"
          }}
        />
      )}
      
      {/* Button content */}
      <span style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </span>
    </motion.button>
  );
};
