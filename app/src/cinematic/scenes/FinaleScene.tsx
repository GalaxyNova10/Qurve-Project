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

// Scene 6: Finale - Orb reforms emotionally, completes the journey
export const FinaleScene: React.FC = () => {
  const navigate = useNavigate();
    const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { createFloatingMotion } = useComponentMotion();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets for emotional finale
  React.useEffect(() => {
    setPreset('hero' as any);
    setLightingPreset('cinematic' as any);
    setAtmospherePreset('nebula_field' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleBeginClick = () => {
    triggerPulse();
    navigate('/register');
  };

  if (!shouldRenderComponent('high')) return null;

  return (
    <motion.section
      className="finale-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Full AI World Background with complete orb */}
      <AIWorld quality="high" />

      {/* Finale Content */}
      <motion.div
        className="finale-content"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 2, ease: "easeOut" }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          maxWidth: '1000px',
          padding: '0 2rem'
        }}
      >
        {/* Finale Headline - Emotional Conclusion */}
        <div className="finale-headline" style={{ marginBottom: '3rem' }}>
          <GlowTypography
            tag="h2"
            text="The Journey"
            variant="large"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.5 }
            }}
          />
          
          <GlowTypography
            tag="h3"
            text="Completes"
            variant="large"
            gradient="cyan-to-purple"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.7 }
            }}
          />
          
          <GlowTypography
            tag="h4"
            text="Here"
            variant="large"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.5, ease: "easeOut", delay: 0.9 }
            }}
          />
        </div>

        {/* Emotional Message */}
        <motion.p
          className="finale-message"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5, delay: 1.1 }}
          style={{
            color: '#E2E8F0',
            fontSize: '1.375rem',
            lineHeight: 1.8,
            marginBottom: '4rem',
            maxWidth: '700px',
            margin: '0 auto 4rem',
            fontWeight: 300,
            textShadow: '0 0 30px rgba(124, 58, 237, 0.3)'
          }}
        >
          From fragments of quantum possibility to a unified intelligence. 
          The AI orb has completed its transformation, now ready to serve your 
          financial journey with wisdom, precision, and unwavering dedication.
        </motion.p>

        {/* Journey Milestones */}
        <motion.div
          className="journey-milestones"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.3 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem'
          }}
        >
          {[
            { phase: 'Arrival', icon: '🌟', complete: true },
            { phase: 'Awakening', icon: '🧠', complete: true },
            { phase: 'Quantum', icon: '⚛️', complete: true },
            { phase: 'Operating System', icon: '⚡', complete: true },
            { phase: 'Trust', icon: '🤝', complete: true },
            { phase: 'Unity', icon: '✨', complete: true }
          ].map((milestone, i) => (
            <motion.div
              key={milestone.phase}
              className="milestone-item"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, ...createFloatingMotion(0.4).animate }}
              transition={{ duration: 0.6, delay: 1.5 + i * 0.1 }}
              style={{
                background: milestone.complete 
                  ? 'rgba(124, 58, 237, 0.1)' 
                  : 'rgba(17, 24, 39, 0.6)',
                backdropFilter: 'blur(20px)',
                border: milestone.complete 
                  ? '1px solid rgba(124, 58, 237, 0.3)' 
                  : '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '1rem',
                padding: '1.5rem',
                textAlign: 'center',
                position: 'relative'
              }}
            >
              {milestone.complete && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.3, delay: 1.6 + i * 0.1 }}
                  style={{
                    position: 'absolute',
                    top: '-8px',
                    right: '-8px',
                    width: '24px',
                    height: '24px',
                    background: '#10B981',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px'
                  }}
                >
                  ✓
                </motion.div>
              )}
              
              <div style={{
                fontSize: '2rem',
                marginBottom: '0.75rem',
                opacity: milestone.complete ? 1 : 0.3
              }}>
                {milestone.icon}
              </div>
              
              <div style={{
                color: milestone.complete ? '#FFFFFF' : '#64748B',
                fontSize: '0.875rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                {milestone.phase}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Final Statistics */}
        <motion.div
          className="final-stats"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5, delay: 2.5 }}
          style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1))',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '1rem',
            padding: '3rem',
            marginBottom: '4rem'
          }}
        >
          <h4 style={{
            color: '#FFFFFF',
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '2rem',
            textAlign: 'center'
          }}>
            Your Journey Begins
          </h4>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '2rem'
          }}>
            {[
              { label: 'Ready Portfolios', value: '∞' },
              { label: 'AI Insights', value: 'Real-time' },
              { label: 'Success Rate', value: '94.7%' },
              { label: 'Your Future', value: 'Bright' }
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                className="final-stat-item"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 2.7 + i * 0.1 }}
                style={{ textAlign: 'center' }}
              >
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.8, 1, 0.8]
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    delay: i * 0.3
                  }}
                  style={{
                    color: '#FFFFFF',
                    fontSize: '2rem',
                    fontWeight: 800,
                    marginBottom: '0.5rem',
                    textShadow: '0 0 20px rgba(124, 58, 237, 0.5)'
                  }}
                >
                  {stat.value}
                </motion.div>
                <div style={{
                  color: '#94A3B8',
                  fontSize: '0.875rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Final CTA */}
        <motion.div
          className="finale-cta"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 3.2 }}
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
            onClick={handleBeginClick}
            {...createFloatingMotion(0.8)}
            style={{
              background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
              fontSize: '1.125rem',
              padding: '1.25rem 3rem',
              boxShadow: '0 0 40px rgba(124, 58, 237, 0.5)'
            }}
          >
            Begin Your Quantum Journey
          </CinematicButton>
          
          <motion.div
            className="completion-indicator"
            style={{
              color: '#E2E8F0',
              fontSize: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}
          >
            <motion.div
              animate={{
                scale: [1, 1.3, 1],
                opacity: [1, 0.5, 1]
              }}
              transition={{
                duration: 2,
                repeat: Infinity
              }}
              style={{
                width: '10px',
                height: '10px',
                background: '#10B981',
                borderRadius: '50%',
                boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)'
              }}
            />
            <span>The Intelligence Awaits Your Command</span>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Celebratory Elements */}
      <div className="finale-celebration">
        {/* Reforming Orb Particles */}
        {Array.from({ length: 50 }, (_, i) => (
          <motion.div
            key={`finale-particle-${i}`}
            className="finale-particle"
            initial={{
              x: window.innerWidth / 2,
              y: window.innerHeight / 2,
              opacity: 0,
              scale: 0
            }}
            animate={{
              x: window.innerWidth / 2 + (Math.random() - 0.5) * 600,
              y: window.innerHeight / 2 + (Math.random() - 0.5) * 600,
              opacity: [0, 1, 0.6],
              scale: [0, 1, 0.8]
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              delay: 4 + i * 0.05,
              ease: "easeOut"
            }}
            style={{
              position: 'absolute',
              width: `${2 + Math.random() * 4}px`,
              height: `${2 + Math.random() * 4}px`,
              background: i % 3 === 0 ? '#7C3AED' : i % 3 === 1 ? '#06B6D4' : '#10B981',
              borderRadius: '50%',
              filter: 'blur(1px)',
              boxShadow: `0 0 ${10 + Math.random() * 20}px rgba(${i % 3 === 0 ? '124, 58, 237' : i % 3 === 1 ? '6, 182, 212' : '16, 185, 129'}, 0.5)`,
              pointerEvents: 'none'
            }}
          />
        ))}
        
        {/* Energy Waves */}
        {Array.from({ length: 5 }, (_, i) => (
          <motion.div
            key={`finale-wave-${i}`}
            className="finale-wave"
            initial={{ scale: 0, opacity: 0.8 }}
            animate={{ scale: [0, 3, 5], opacity: [0.8, 0.3, 0] }}
            transition={{
              duration: 4 + i * 0.5,
              delay: 4 + i * 0.3,
              ease: "easeOut"
            }}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '200px',
              height: '200px',
              border: '2px solid rgba(124, 58, 237, 0.3)',
              borderRadius: '50%',
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>
    </motion.section>
  );
};
