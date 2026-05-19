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

// Scene 3: Quantum - Fragments power GPU processing scene
export const QuantumScene: React.FC = () => {
  const navigate = useNavigate();
    const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { createFloatingMotion } = useComponentMotion();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets
  React.useEffect(() => {
    setPreset('technical' as any);
    setLightingPreset('cyberpunk' as any);
    setAtmospherePreset('cyber_space' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleExperienceClick = () => {
    triggerPulse();
    navigate('/register');
  };

  if (!shouldRenderComponent('medium')) return null;

  return (
    <motion.section
      className="quantum-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* AI World Background with enhanced GPU effects */}
      <AIWorld quality="high" />

      {/* Quantum Processing Content */}
      <motion.div
        className="quantum-content"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          maxWidth: '1200px',
          padding: '0 2rem'
        }}
      >
        {/* Quantum Headline */}
        <div className="quantum-headline" style={{ marginBottom: '3rem' }}>
          <GlowTypography
            tag="h2"
            text="Quantum"
            variant="large"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.2, ease: "easeOut", delay: 0.3 }
            }}
          />
          
          <GlowTypography
            tag="h3"
            text="Processing"
            variant="large"
            gradient="cyan-to-purple"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.2, ease: "easeOut", delay: 0.5 }
            }}
          />
        </div>

        {/* Quantum Description */}
        <motion.p
          className="quantum-description"
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
            textShadow: '0 0 20px rgba(124, 58, 237, 0.3)'
          }}
        >
          Harness the power of quantum computing to process infinite possibilities simultaneously. 
          Our GPU-accelerated neural networks analyze market data at the speed of light, 
          delivering insights that traditional systems can never achieve.
        </motion.p>

        {/* Processing Metrics */}
        <motion.div
          className="processing-metrics"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem'
          }}
        >
          {[
            { label: 'Quantum Operations', value: '10²⁴', unit: '/sec', color: '#7C3AED' },
            { label: 'GPU Cores', value: '4096', unit: 'active', color: '#06B6D4' },
            { label: 'Processing Speed', value: '99.9', unit: '%', color: '#8B5CF6' },
            { label: 'Neural Pathways', value: '∞', unit: 'connections', color: '#7C3AED' }
          ].map((metric, i) => (
            <motion.div
              key={metric.label}
              className="metric-card"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, ...createFloatingMotion(0.4).animate }}
              transition={{ duration: 0.6, delay: 1.1 + i * 0.1 }}
              style={{
                background: 'rgba(17, 24, 39, 0.8)',
                backdropFilter: 'blur(20px)',
                border: `1px solid ${metric.color}33`,
                borderRadius: '1rem',
                padding: '1.5rem',
                textAlign: 'center',
                boxShadow: `0 0 20px ${metric.color}33`
              }}
            >
              <div style={{
                color: metric.color,
                fontSize: '2rem',
                fontWeight: '800',
                marginBottom: '0.5rem',
                textShadow: `0 0 20px ${metric.color}`
              }}>
                {metric.value}
              </div>
              <div style={{
                color: '#64748B',
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '0.25rem'
              }}>
                {metric.label}
              </div>
              <div style={{
                color: '#94A3B8',
                fontSize: '0.875rem'
              }}>
                {metric.unit}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Algorithm Grid */}
        <motion.div
          className="algorithm-grid"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.3 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem',
            marginBottom: '4rem'
          }}
        >
          {[
            { name: 'Monte Carlo', status: 'Optimizing', progress: 87 },
            { name: 'Neural Networks', status: 'Learning', progress: 92 },
            { name: 'Genetic Algorithms', status: 'Evolving', progress: 78 },
            { name: 'Deep Learning', status: 'Training', progress: 95 }
          ].map((algo, i) => (
            <motion.div
              key={algo.name}
              className="algorithm-card"
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 1.5 + i * 0.1 }}
              style={{
                background: 'rgba(17, 24, 39, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '0.75rem',
                padding: '1.5rem',
                textAlign: 'left'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h4 style={{
                  color: '#FFFFFF',
                  fontSize: '1rem',
                  fontWeight: 600
                }}>
                  {algo.name}
                </h4>
                <motion.div
                  animate={{
                    opacity: [0.5, 1, 0.5]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.2
                  }}
                  style={{
                    color: '#10B981',
                    fontSize: '0.75rem',
                    fontWeight: 500
                  }}
                >
                  {algo.status}
                </motion.div>
              </div>
              <div style={{
                height: '4px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '2px',
                overflow: 'hidden',
                marginBottom: '0.5rem'
              }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${algo.progress}%` }}
                  transition={{
                    duration: 2,
                    delay: 1.7 + i * 0.1,
                    ease: "easeOut"
                  }}
                  style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, #7C3AED, #06B6D4)',
                    borderRadius: '2px'
                  }}
                />
              </div>
              <div style={{
                color: '#64748B',
                fontSize: '0.75rem',
                textAlign: 'right'
              }}>
                {algo.progress}%
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Section */}
        <motion.div
          className="quantum-cta"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.8 }}
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
            onClick={handleExperienceClick}
            {...createFloatingMotion(0.7)}
          >
            Access Quantum Processing
          </CinematicButton>
          
          <motion.div
            className="processing-indicator"
            style={{
              color: '#64748B',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}
          >
            <motion.div
              animate={{
                opacity: [1, 0.3, 1]
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity
              }}
              style={{
                width: '8px',
                height: '8px',
                background: '#10B981',
                borderRadius: '50%'
              }}
            />
            <span>Systems Operating at Peak Efficiency</span>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Quantum Particles */}
      <div className="quantum-particles">
        {Array.from({ length: 30 }, (_, i) => (
          <motion.div
            key={`quantum-${i}`}
            className="quantum-particle"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: 0
            }}
            animate={{
              x: [
                Math.random() * window.innerWidth,
                Math.random() * window.innerWidth,
                Math.random() * window.innerWidth
              ],
              y: [
                Math.random() * window.innerHeight,
                Math.random() * window.innerHeight,
                Math.random() * window.innerHeight
              ],
              opacity: [0, 0.8, 0]
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2
            }}
            style={{
              position: 'absolute',
              width: '2px',
              height: '2px',
              background: i % 2 === 0 ? '#7C3AED' : '#06B6D4',
              borderRadius: '50%',
              filter: 'blur(0.5px)',
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>

      {/* Processing Grid */}
      <div className="processing-grid">
        {Array.from({ length: 8 }, (_, i) => (
          <motion.div
            key={`grid-${i}`}
            className="grid-line"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 0.1, scale: 1 }}
            transition={{
              duration: 1,
              delay: 2 + i * 0.1
            }}
            style={{
              position: 'absolute',
              top: `${20 + (i % 4) * 20}%`,
              left: `${20 + Math.floor(i / 4) * 60}%`,
              width: '40%',
              height: '1px',
              background: 'linear-gradient(90deg, transparent, #7C3AED, transparent)',
              transform: `rotate(${i % 2 === 0 ? 45 : -45}deg)`,
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>
    </motion.section>
  );
};
