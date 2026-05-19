import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useLighting } from '../core/LightingEngine';
import { useComponentMotion } from '../core/MotionEngine';
import { usePerformance } from '../core/PerformanceDirector';

// Magnetic CTA Types
export type CTAVariant = 'primary' | 'secondary' | 'floating' | 'magnetic' | 'quantum';
export type CTASize = 'small' | 'medium' | 'large' | 'massive';

interface MagneticCTAProps {
  children: React.ReactNode;
  variant?: CTAVariant;
  size?: CTASize;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  href?: string;
  target?: string;
  glowIntensity?: number;
  magneticStrength?: number;
}

// Magnetic CTA Component
export const MagneticCTA: React.FC<MagneticCTAProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  onClick,
  disabled = false,
  className = '',
  style = {},
  href,
  target,
  glowIntensity = 1,
  magneticStrength = 0.3,
  ...props
}) => {
  const navigate = useNavigate();
  const { triggerPulse } = useLighting();
  const { createFloatingMotion, getSpringConfig } = useComponentMotion();
  const { shouldRenderComponent } = usePerformance();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  // Handle magnetic effect
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!buttonRef.current || disabled) return;
    
    const rect = buttonRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = (e.clientX - centerX) * magneticStrength;
    const deltaY = (e.clientY - centerY) * magneticStrength;
    
    setMousePosition({ x: deltaX, y: deltaY });
  };

  const handleMouseLeave = () => {
    setMousePosition({ x: 0, y: 0 });
    setIsHovered(false);
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleClick = () => {
    if (disabled) return;
    
    triggerPulse();
    
    if (href) {
      if (target === '_blank') {
        window.open(href, '_blank');
      } else {
        navigate(href);
      }
    } else if (onClick) {
      onClick();
    }
  };

  if (!shouldRenderComponent('medium')) return null;

  // Size styles
  const sizeStyles = {
    small: {
      padding: '0.75rem 1.5rem',
      fontSize: '0.875rem',
      borderRadius: '0.5rem'
    },
    medium: {
      padding: '1rem 2rem',
      fontSize: '1rem',
      borderRadius: '0.75rem'
    },
    large: {
      padding: '1.25rem 2.5rem',
      fontSize: '1.125rem',
      borderRadius: '1rem'
    },
    massive: {
      padding: '1.5rem 3rem',
      fontSize: '1.25rem',
      borderRadius: '1.25rem'
    }
  };

  // Variant styles
  const variantStyles = {
    primary: {
      background: 'linear-gradient(135deg, #7C3AED, #6D28D9)',
      color: '#FFFFFF',
      border: 'none',
      boxShadow: `0 0 ${20 * glowIntensity}px rgba(124, 58, 237, 0.5), 0 0 ${40 * glowIntensity}px rgba(124, 58, 237, 0.2)`
    },
    secondary: {
      background: 'transparent',
      color: '#FFFFFF',
      border: '1px solid rgba(124, 58, 237, 0.5)',
      boxShadow: `0 0 ${10 * glowIntensity}px rgba(124, 58, 237, 0.3)`
    },
    floating: {
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1))',
      backdropFilter: 'blur(20px)',
      color: '#FFFFFF',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      boxShadow: `0 0 ${15 * glowIntensity}px rgba(124, 58, 237, 0.3)`
    },
    magnetic: {
      background: 'linear-gradient(135deg, #06B6D4, #7C3AED)',
      color: '#FFFFFF',
      border: 'none',
      boxShadow: `0 0 ${25 * glowIntensity}px rgba(6, 182, 212, 0.5), 0 0 ${50 * glowIntensity}px rgba(124, 58, 237, 0.3)`
    },
    quantum: {
      background: 'radial-gradient(circle, rgba(124, 58, 237, 0.2), transparent)',
      color: '#FFFFFF',
      border: '2px solid rgba(124, 58, 237, 0.5)',
      boxShadow: `0 0 ${30 * glowIntensity}px rgba(124, 58, 237, 0.4), inset 0 0 ${20 * glowIntensity}px rgba(124, 58, 237, 0.2)`
    }
  };

  return (
    <motion.button
      ref={buttonRef}
      className={`magnetic-cta ${className}`}
      disabled={disabled}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        position: 'relative',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontFamily: 'Inter, system-ui, sans-serif',
        fontWeight: 600,
        letterSpacing: '0.025em',
        textTransform: 'uppercase',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        ...sizeStyles[size],
        ...variantStyles[variant],
        ...style,
        transform: `translate(${mousePosition.x}px, ${mousePosition.y}px)`,
        opacity: disabled ? 0.5 : 1
      }}
      whileHover={!disabled ? {
        scale: 1.05,
        boxShadow: variant === 'primary' 
          ? `0 0 ${30 * glowIntensity}px rgba(124, 58, 237, 0.7), 0 0 ${60 * glowIntensity}px rgba(124, 58, 237, 0.3)`
          : variant === 'magnetic'
          ? `0 0 ${40 * glowIntensity}px rgba(6, 182, 212, 0.7), 0 0 ${80 * glowIntensity}px rgba(124, 58, 237, 0.4)`
          : `0 0 ${25 * glowIntensity}px rgba(124, 58, 237, 0.5), 0 0 ${50 * glowIntensity}px rgba(124, 58, 237, 0.2)`,
        transition: { ...getSpringConfig() }
      } : {}}
      whileTap={!disabled ? {
        scale: 0.98,
        transition: { duration: 0.1 }
      } : {}}
      animate={{ ...createFloatingMotion(0.5).animate }}
      transition={{ ...createFloatingMotion(0.5).transition, ease: 'easeInOut' as const }}
      {...props}
    >
      {/* Magnetic Field Effect */}
      {isHovered && (
        <motion.div
          className="magnetic-field"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 0.3, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '200%',
            height: '200%',
            background: 'radial-gradient(circle, rgba(124, 58, 237, 0.2), transparent)',
            pointerEvents: 'none'
          }}
        />
      )}
      
      {/* Energy Particles */}
      {variant === 'quantum' && isHovered && (
        <div className="quantum-particles">
          {Array.from({ length: 8 }, (_, i) => (
            <motion.div
              key={`particle-${i}`}
              className="quantum-particle"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              style={{
                position: 'absolute',
                top: `${20 + Math.random() * 60}%`,
                left: `${20 + Math.random() * 60}%`,
                width: '2px',
                height: '2px',
                background: '#7C3AED',
                borderRadius: '50%',
                filter: 'blur(1px)',
                pointerEvents: 'none'
              }}
            />
          ))}
        </div>
      )}
      
      {/* Animated Background Gradient */}
      {variant === 'primary' && (
        <motion.div
          className="cta-gradient"
          animate={{
            background: [
              'linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
              'linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
              'linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent)'
            ]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            transform: 'translateX(-100%)'
          }}
        />
      )}
      
      {/* Button Content */}
      <span style={{ 
        position: 'relative', 
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        {children}
        {variant === 'quantum' && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            style={{
              width: '16px',
              height: '16px',
              border: '2px solid currentColor',
              borderTopColor: 'transparent',
              borderRadius: '50%'
            }}
          />
        )}
      </span>
    </motion.button>
  );
};

// Specialized CTA Components
export const HeroCTA: React.FC<{ children: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
  <MagneticCTA
    variant="primary"
    size="massive"
    onClick={onClick}
    glowIntensity={1.5}
    magneticStrength={0.4}
    style={{
      fontSize: '1.5rem',
      padding: '2rem 4rem',
      background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
      boxShadow: '0 0 60px rgba(124, 58, 237, 0.6), 0 0 120px rgba(124, 58, 237, 0.3)'
    }}
  >
    {children}
  </MagneticCTA>
);

export const FloatingCTA: React.FC<{ children: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
  <MagneticCTA
    variant="floating"
    size="large"
    onClick={onClick}
    glowIntensity={0.8}
    style={{
      backdropFilter: 'blur(30px)',
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(6, 182, 212, 0.15))',
      border: '1px solid rgba(255, 255, 255, 0.2)'
    }}
  >
    {children}
  </MagneticCTA>
);

export const QuantumCTA: React.FC<{ children: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
  <MagneticCTA
    variant="quantum"
    size="large"
    onClick={onClick}
    glowIntensity={1.2}
    magneticStrength={0.5}
    style={{
      background: 'radial-gradient(circle, rgba(124, 58, 237, 0.3), transparent)',
      border: '2px solid rgba(124, 58, 237, 0.6)',
      boxShadow: '0 0 40px rgba(124, 58, 237, 0.5), inset 0 0 30px rgba(124, 58, 237, 0.3)'
    }}
  >
    {children}
  </MagneticCTA>
);

export const TrustCTA: React.FC<{ children: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
  <MagneticCTA
    variant="secondary"
    size="medium"
    onClick={onClick}
    glowIntensity={0.5}
    style={{
      background: 'transparent',
      border: '1px solid rgba(124, 58, 237, 0.3)',
      color: '#E2E8F0',
      fontWeight: 500
    }}
  >
    {children}
  </MagneticCTA>
);

// Hook for magnetic CTA interactions
export const useMagneticCTA = () => {
  const { triggerPulse } = useLighting();
  const { createFloatingMotion } = useComponentMotion();

  const createMagneticEffect = () => ({
    whileHover: {
      scale: 1.05,
      transition: { duration: 0.3, ease: "easeOut" }
    },
    whileTap: {
      scale: 0.98,
      transition: { duration: 0.1 }
    },
    onTap: () => triggerPulse()
  });

  const createQuantumEffect = () => ({
    ...createFloatingMotion(0.8),
    whileHover: {
      scale: 1.1,
      boxShadow: '0 0 40px rgba(124, 58, 237, 0.6), 0 0 80px rgba(6, 182, 212, 0.4)',
      transition: { duration: 0.3 }
    }
  });

  return {
    createMagneticEffect,
    createQuantumEffect
  };
};
