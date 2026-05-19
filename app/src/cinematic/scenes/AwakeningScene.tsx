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

// Scene 2: Awakening - AI orb fragments evolve and intelligence awakens
export const AwakeningScene: React.FC = () => {
  const navigate = useNavigate();
  const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { createFloatingMotion } = useComponentMotion();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets
  React.useEffect(() => {
    setPreset('intimate' as any);
    setLightingPreset('atmospheric' as any);
    setAtmospherePreset('nebula_field' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleExploreClick = () => {
    triggerPulse();
    navigate('/register');
  };

  if (!shouldRenderComponent('medium')) return null;

  return (
    <motion.section
      className="awakening-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* AI World Background with evolving orb */}
      <AIWorld quality="medium" />

      {/* Awakening Content */}
      <motion.div
        className="awakening-content"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          maxWidth: '1000px',
          padding: '0 2rem'
        }}
      >
        {/* Awakening Headline */}
        <div className="awakening-headline" style={{ marginBottom: '3rem' }}>
          <GlowTypography
            tag="h2"
            text="The Intelligence"
            variant="large"
            gradient="cyan-to-purple"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.2, ease: "easeOut", delay: 0.3 }
            }}
          />
          
          <GlowTypography
            tag="h3"
            text="Awakens"
            variant="large"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.2, ease: "easeOut", delay: 0.5 }
            }}
          />
        </div>

        {/* Awakening Description */}
        <motion.p
          className="awakening-description"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.7 }}
          style={{
            color: '#94A3B8',
            fontSize: '1.125rem',
            lineHeight: 1.7,
            marginBottom: '4rem',
            maxWidth: '700px',
            margin: '0 auto 4rem',
            textShadow: '0 0 20px rgba(6, 182, 212, 0.3)'
          }}
        >
          Watch as quantum intelligence fragments coalesce into conscious awareness. 
          Each algorithm learns, adapts, and evolves, creating a neural network that 
          transcends traditional computing boundaries.
        </motion.p>

        {/* Awakening Features Grid */}
        <motion.div
          className="awakening-features"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem'
          }}
        >
          {[
            {
              title: 'Neural Evolution',
              description: 'Self-learning algorithms that adapt to market patterns',
              icon: '🧠'
            },
            {
              title: 'Quantum Processing',
              description: 'Simultaneous calculation of infinite possibilities',
              icon: '⚛️'
            },
            {
              title: 'Predictive Analytics',
              description: 'Forecast market movements with unprecedented accuracy',
              icon: '📊'
            }
          ].map((feature, i) => (
            <motion.div
              key={feature.title}
              className="feature-card"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, ...createFloatingMotion(0.3).animate }}
              transition={{ duration: 0.6, delay: 1.1 + i * 0.1 }}
              style={{
                background: 'rgba(17, 24, 39, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '1rem',
                padding: '2rem',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>
                {feature.icon}
              </div>
              <h4 style={{
                color: '#FFFFFF',
                fontSize: '1.125rem',
                fontWeight: 600,
                marginBottom: '0.75rem'
              }}>
                {feature.title}
              </h4>
              <p style={{
                color: '#94A3B8',
                fontSize: '0.875rem',
                lineHeight: 1.5
              }}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Section */}
        <motion.div
          className="awakening-cta"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.4 }}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2rem'
          }}
        >
          <CinematicButton
            variant="primary"
            size="large"
            onClick={handleExploreClick}
            {...createFloatingMotion(0.6)}
          >
            Experience the Awakening
          </CinematicButton>
          
          <motion.div
            className="scroll-indicator"
            animate={{
              y: [0, 10, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            style={{
              color: '#64748B',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <span>Continue to Quantum Processing</span>
            <div style={{
              width: '20px',
              height: '1px',
              background: '#64748B'
            }} />
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Floating Fragments */}
      <div className="awakening-fragments">
        {Array.from({ length: 12 }, (_, i) => (
          <motion.div
            key={`fragment-${i}`}
            className="fragment"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: 0,
              scale: 0
            }}
            animate={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: [0, 0.6, 0.3],
              scale: [0, 1, 0.8],
              rotate: [0, 180, 360]
            }}
            transition={{
              duration: 8 + Math.random() * 4,
              repeat: Infinity,
              delay: Math.random() * 2,
              ease: "easeInOut"
            }}
            style={{
              position: 'absolute',
              width: `${4 + Math.random() * 8}px`,
              height: `${4 + Math.random() * 8}px`,
              background: i % 3 === 0 ? '#7C3AED' : i % 3 === 1 ? '#06B6D4' : '#8B5CF6',
              borderRadius: '50%',
              filter: 'blur(1px)',
              boxShadow: `0 0 ${10 + Math.random() * 20}px rgba(${i % 3 === 0 ? '124, 58, 237' : i % 3 === 1 ? '6, 182, 212' : '139, 92, 246'}, 0.5)`,
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>

      {/* Energy Waves */}
      <motion.div
        className="energy-waves"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
        transition={{ duration: 2, delay: 1 }}
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '600px',
          height: '600px',
          pointerEvents: 'none'
        }}
      >
        {Array.from({ length: 3 }, (_, i) => (
          <motion.div
            key={`wave-${i}`}
            className="wave"
            initial={{ scale: 0.5, opacity: 0.6 }}
            animate={{
              scale: [0.5, 2, 0.5],
              opacity: [0.6, 0, 0.6]
            }}
            transition={{
              duration: 4 + i * 1,
              repeat: Infinity,
              delay: i * 0.5,
              ease: "easeOut"
            }}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              border: '2px solid rgba(124, 58, 237, 0.3)',
              borderRadius: '50%',
              transform: `scale(${1 + i * 0.3})`
            }}
          />
        ))}
      </motion.div>
    </motion.section>
  );
};
