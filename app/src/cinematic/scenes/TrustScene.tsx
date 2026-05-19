import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useCamera } from '../core/CameraDirector';
import { useLighting } from '../core/LightingEngine';
import { useAtmosphere } from '../core/AtmosphereEngine';
import { usePerformance } from '../core/PerformanceDirector';
import { AIWorld } from '../environment/AIWorld';
import { CinematicButton } from '../ui/CinematicButton';
import { GlowTypography } from '../ui/GlowTypography';

// Scene 5: Trust - Visual silence moments and trust building
export const TrustScene: React.FC = () => {
  const navigate = useNavigate();
  const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets for calm, trusting atmosphere
  React.useEffect(() => {
    setPreset('atmospheric' as any);
    setLightingPreset('atmospheric' as any);
    setAtmospherePreset('atmospheric_dream' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleTrustClick = () => {
    triggerPulse();
    navigate('/register');
  };

  if (!shouldRenderComponent('medium')) return null;

  return (
    <motion.section
      className="trust-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Minimal AI World Background */}
      <AIWorld quality="low" />

      {/* Trust Content - Visual Silence */}
      <motion.div
        className="trust-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2, ease: "easeOut" }}
        style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          maxWidth: '800px',
          padding: '0 2rem'
        }}
      >
        {/* Trust Headline - Simple and Clean */}
        <div className="trust-headline" style={{ marginBottom: '4rem' }}>
          <GlowTypography
            tag="h2"
            text="Trust"
            variant="large"
            gradient="purple"
            animate={{
              initial: { opacity: 0, y: 30 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 2, ease: "easeOut", delay: 0.8 }
            }}
          />
          
          <motion.div
            style={{
              width: '60px',
              height: '1px',
              background: 'linear-gradient(90deg, transparent, #7C3AED, transparent)',
              margin: '2rem auto',
              opacity: 0.3
            }}
          />
          
          <GlowTypography
            tag="h3"
            text="in Intelligence"
            variant="medium"
            gradient="cyan"
            animate={{
              initial: { opacity: 0, y: 30 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 2, ease: "easeOut", delay: 1.2 }
            }}
          />
        </div>

        {/* Trust Message - Minimal and Direct */}
        <motion.p
          className="trust-message"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 1.6 }}
          style={{
            color: '#94A3B8',
            fontSize: '1.25rem',
            lineHeight: 1.8,
            marginBottom: '4rem',
            maxWidth: '600px',
            margin: '0 auto 4rem',
            fontWeight: 300
          }}
        >
          In a world of complexity, we bring clarity. Our AI operates with transparency, 
          ethics, and your trust at its core. Every decision is explainable, every outcome 
          is verifiable.
        </motion.p>

        {/* Trust Pillars - Simple Grid */}
        <motion.div
          className="trust-pillars"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.5, delay: 2 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '3rem',
            marginBottom: '4rem'
          }}
        >
          {[
            {
              icon: '🔒',
              title: 'Security',
              description: 'Bank-level encryption protects your data'
            },
            {
              icon: '👁️',
              title: 'Transparency',
              description: 'Every recommendation is explainable'
            },
            {
              icon: '⚖️',
              title: 'Ethics',
              description: 'AI operates with human values'
            }
          ].map((pillar, i) => (
            <motion.div
              key={pillar.title}
              className="pillar-item"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, delay: 2.5 + i * 0.3 }}
              style={{ textAlign: 'center' }}
            >
              <motion.div
                animate={{
                  scale: [1, 1.1, 1]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  delay: i * 0.5,
                  ease: "easeInOut"
                }}
                style={{
                  fontSize: '2.5rem',
                  marginBottom: '1rem',
                  opacity: 0.8
                }}
              >
                {pillar.icon}
              </motion.div>
              <h4 style={{
                color: '#FFFFFF',
                fontSize: '1.125rem',
                fontWeight: 500,
                marginBottom: '0.5rem'
              }}>
                {pillar.title}
              </h4>
              <p style={{
                color: '#64748B',
                fontSize: '0.875rem',
                lineHeight: 1.5
              }}>
                {pillar.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* Security Metrics - Minimal Display */}
        <motion.div
          className="security-metrics"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 3.5 }}
          style={{
            background: 'rgba(17, 24, 39, 0.4)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '1rem',
            padding: '2rem',
            marginBottom: '4rem'
          }}
        >
          <div style={{
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '2rem'
          }}>
            {[
              { label: 'Data Encrypted', value: '100%' },
              { label: 'Privacy Compliant', value: 'GDPR' },
              { label: 'Audit Trail', value: 'Complete' },
              { label: 'Uptime', value: '99.99%' }
            ].map((metric, i) => (
              <motion.div
                key={metric.label}
                className="security-item"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 4 + i * 0.2 }}
                style={{ textAlign: 'center' }}
              >
                <div style={{
                  color: '#10B981',
                  fontSize: '1.25rem',
                  fontWeight: 600,
                  marginBottom: '0.5rem'
                }}>
                  {metric.value}
                </div>
                <div style={{
                  color: '#64748B',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  {metric.label}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* CTA - Gentle and Trusting */}
        <motion.div
          className="trust-cta"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 4.5 }}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2rem'
          }}
        >
          <CinematicButton
            variant="secondary"
            size="large"
            onClick={handleTrustClick}
            style={{
              background: 'transparent',
              border: '1px solid rgba(124, 58, 237, 0.3)',
              color: '#FFFFFF'
            }}
          >
            Begin Your Journey
          </CinematicButton>
          
          <motion.div
            className="trust-indicator"
            style={{
              color: '#64748B',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <motion.div
              animate={{
                opacity: [0.3, 0.8, 0.3]
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              style={{
                width: '6px',
                height: '6px',
                background: '#10B981',
                borderRadius: '50%'
              }}
            />
            <span>Your trust is our foundation</span>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Minimal Visual Elements */}
      <div className="trust-visuals">
        {/* Subtle Particles */}
        {Array.from({ length: 8 }, (_, i) => (
          <motion.div
            key={`trust-particle-${i}`}
            className="trust-particle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.1 }}
            transition={{
              duration: 3,
              delay: 2 + i * 0.5
            }}
            style={{
              position: 'absolute',
              top: `${20 + Math.random() * 60}%`,
              left: `${20 + Math.random() * 60}%`,
              width: '2px',
              height: '2px',
              background: '#7C3AED',
              borderRadius: '50%',
              filter: 'blur(2px)',
              pointerEvents: 'none'
            }}
          />
        ))}
        
        {/* Gentle Glow */}
        <motion.div
          className="gentle-glow"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.05 }}
          transition={{ duration: 4, delay: 1 }}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '600px',
            height: '600px',
            background: 'radial-gradient(circle, rgba(124, 58, 237, 0.1), transparent)',
            borderRadius: '50%',
            pointerEvents: 'none'
          }}
        />
      </div>
    </motion.section>
  );
};
