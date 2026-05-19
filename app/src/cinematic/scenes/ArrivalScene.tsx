import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useCamera } from '../core/CameraDirector';
import { useLighting } from '../core/LightingEngine';
import { useComponentMotion } from '../core/MotionEngine';
import { useAtmosphere } from '../core/AtmosphereEngine';
import { usePerformance } from '../core/PerformanceDirector';
import { AIWorld } from '../environment/AIWorld';
import { CinematicButton } from '../ui/CinematicButton';
import { GlowTypography } from '../ui/GlowTypography';

// Scene 1: Arrival - Massive immersive hero experience
export const ArrivalScene: React.FC = () => {
  const navigate = useNavigate();
    const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { createFloatingMotion, createVelocityReaction } = useComponentMotion();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets
  React.useEffect(() => {
    setPreset('cinematic' as any);
    setLightingPreset('cinematic' as any);
    setAtmospherePreset('deep_space' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleCTAClick = () => {
    triggerPulse();
    // Navigate to next scene or auth
    navigate('/register');
  };

  if (!shouldRenderComponent('high')) return null;

  return (
    <motion.section
      className="arrival-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* AI World Background */}
      <AIWorld quality="high" />

      {/* Hero Content Container */}
      <motion.div
        className="hero-content"
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          maxWidth: '1200px',
          padding: '0 2rem'
        }}
      >
        {/* Cinematic Typography */}
        <div className="hero-headline" style={{ marginBottom: '3rem' }}>
          <GlowTypography
            tag="h1"
            text="Intelligence."
            variant="massive"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 100 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.2 }
            }}
          />
          
          <GlowTypography
            tag="h2"
            text="Engineered"
            variant="massive"
            gradient="cyan-to-purple"
            animate={{
              initial: { opacity: 0, y: 100 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.4 }
            }}
          />
          
          <GlowTypography
            tag="h3"
            text="for Alpha."
            variant="massive"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 100 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.6 }
            }}
          />
        </div>

        {/* Subtitle */}
        <motion.p
          className="hero-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
          style={{
            color: '#94A3B8',
            fontSize: '1.25rem',
            lineHeight: 1.6,
            marginBottom: '4rem',
            maxWidth: '600px',
            margin: '0 auto 4rem',
            textShadow: '0 0 20px rgba(124, 58, 237, 0.3)'
          }}
        >
          Experience the future of portfolio optimization through quantum intelligence 
          and neural computing. Qurve transforms complexity into clarity.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          className="cta-container"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1 }}
          style={{
            display: 'flex',
            gap: '2rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}
        >
          <CinematicButton
            variant="primary"
            size="large"
            onClick={handleCTAClick}
            {...createFloatingMotion(0.8)}
          >
            Begin Intelligence Journey
          </CinematicButton>
          
          <CinematicButton
            variant="secondary"
            size="large"
            onClick={() => navigate('/login')}
            {...createFloatingMotion(0.6)}
          >
            Access System
          </CinematicButton>
        </motion.div>

        {/* Trust Banner */}
        <motion.div
          className="trust-banner"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.2 }}
          style={{
            position: 'absolute',
            bottom: '4rem',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '3rem',
            alignItems: 'center'
          }}
        >
          {['NVIDIA', 'Bloomberg', 'Reuters', 'Financial Times'].map((partner, i) => (
            <motion.div
              key={partner}
              className="partner-logo"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 0.3, ...createVelocityReaction().animate }}
              transition={{ duration: 0.6, delay: 1.4 + i * 0.1, type: 'spring' as const }}
              style={{
                color: '#64748B',
                fontSize: '0.875rem',
                fontWeight: 600,
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                opacity: 0.3
              }}
            >
              {partner}
            </motion.div>
          ))}
        </motion.div>
      </motion.div>

      {/* Floating Metrics */}
      <motion.div
        className="floating-metrics"
        style={{
          position: 'absolute',
          top: '20%',
          right: '10%',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem'
        }}
      >
        {[
          { label: 'Expected Return', value: '+24.7%', change: '+2.3%' },
          { label: 'Risk Score', value: '0.42', change: '-0.08' },
          { label: 'Sharpe Ratio', value: '2.34', change: '+0.15' }
        ].map((metric, i) => (
          <motion.div
            key={metric.label}
            className="metric-card"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, ...createFloatingMotion(0.5).animate }}
            transition={{ duration: 0.6, delay: 0.8 + i * 0.2 }}
            style={{
              background: 'rgba(17, 24, 39, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '1rem',
              padding: '1rem 1.5rem',
              minWidth: '200px'
            }}
          >
            <div style={{ color: '#64748B', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
              {metric.label}
            </div>
            <div style={{ 
              color: '#FFFFFF', 
              fontSize: '1.5rem', 
              fontWeight: '700',
              marginBottom: '0.25rem'
            }}>
              {metric.value}
            </div>
            <div style={{ 
              color: metric.change.startsWith('+') ? '#10B981' : '#EF4444',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {metric.change}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Ambient Particles */}
      <div className="ambient-particles">
        {Array.from({ length: 20 }, (_, i) => (
          <motion.div
            key={`particle-${i}`}
            className="particle"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: 0
            }}
            animate={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: [0, 0.6, 0]
            }}
            transition={{
              duration: 10 + Math.random() * 10,
              repeat: Infinity,
              delay: Math.random() * 5
            }}
            style={{
              position: 'absolute',
              width: '3px',
              height: '3px',
              background: i % 2 === 0 ? '#7C3AED' : '#06B6D4',
              borderRadius: '50%',
              filter: 'blur(1px)',
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>
    </motion.section>
  );
};
