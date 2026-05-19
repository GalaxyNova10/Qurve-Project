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

// Scene 4: Operating System - Orb becomes neural core
export const OperatingSystemScene: React.FC = () => {
  const navigate = useNavigate();
    const { setPreset } = useCamera();
  const { setPreset: setLightingPreset, triggerPulse } = useLighting();
  const { createFloatingMotion } = useComponentMotion();
  const { setPreset: setAtmospherePreset } = useAtmosphere();
  const { shouldRenderComponent } = usePerformance();

  // Set scene-specific presets
  React.useEffect(() => {
    setPreset('cinematic' as any);
    setLightingPreset('clinical' as any);
    setAtmospherePreset('cyber_space' as any);
  }, [setPreset, setLightingPreset, setAtmospherePreset]);

  const handleSystemClick = () => {
    triggerPulse();
    navigate('/register');
  };

  if (!shouldRenderComponent('medium')) return null;

  return (
    <motion.section
      className="operating-system-scene"
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* AI World Background with neural core */}
      <AIWorld quality="medium" />

      {/* Operating System Content */}
      <motion.div
        className="os-content"
        initial={{ opacity: 0, scale: 0.9 }}
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
        {/* OS Headline */}
        <div className="os-headline" style={{ marginBottom: '3rem' }}>
          <GlowTypography
            tag="h2"
            text="Neural"
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
            text="Operating System"
            variant="large"
            gradient="purple-to-cyan"
            animate={{
              initial: { opacity: 0, y: 50 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 1.2, ease: "easeOut", delay: 0.5 }
            }}
          />
        </div>

        {/* OS Description */}
        <motion.p
          className="os-description"
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
            textShadow: '0 0 20px rgba(139, 92, 246, 0.3)'
          }}
        >
          The AI orb has evolved into a neural operating system, processing billions of data points 
          in real-time. This is the foundation of intelligent portfolio management, where every 
          decision is optimized by machine consciousness.
        </motion.p>

        {/* System Architecture */}
        <motion.div
          className="system-architecture"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem'
          }}
        >
          {[
            {
              layer: 'Core Intelligence',
              function: 'Decision Making & Analysis',
              status: 'ACTIVE',
              connections: 2048
            },
            {
              layer: 'Neural Network',
              function: 'Pattern Recognition & Learning',
              status: 'LEARNING',
              connections: 4096
            },
            {
              layer: 'Data Processing',
              function: 'Real-time Market Analysis',
              status: 'OPTIMIZED',
              connections: 8192
            },
            {
              layer: 'Interface Layer',
              function: 'User Interaction & Output',
              status: 'READY',
              connections: 1024
            }
          ].map((layer, i) => (
            <motion.div
              key={layer.layer}
              className="layer-card"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, ...createFloatingMotion(0.3).animate }}
              transition={{ duration: 0.6, delay: 1.1 + i * 0.1 }}
              style={{
                background: 'rgba(17, 24, 39, 0.8)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '1rem',
                padding: '2rem',
                textAlign: 'left',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {/* Connection Lines */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '2px',
                background: `linear-gradient(90deg, transparent, #8B5CF6, transparent)`,
                opacity: 0.5
              }} />
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '1rem'
              }}>
                <div>
                  <h4 style={{
                    color: '#FFFFFF',
                    fontSize: '1.125rem',
                    fontWeight: 600,
                    marginBottom: '0.5rem'
                  }}>
                    {layer.layer}
                  </h4>
                  <p style={{
                    color: '#94A3B8',
                    fontSize: '0.875rem',
                    lineHeight: 1.4
                  }}>
                    {layer.function}
                  </p>
                </div>
                <motion.div
                  animate={{
                    opacity: [0.5, 1, 0.5]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.3
                  }}
                  style={{
                    padding: '0.25rem 0.75rem',
                    background: 'rgba(139, 92, 246, 0.2)',
                    border: '1px solid rgba(139, 92, 246, 0.5)',
                    borderRadius: '9999px',
                    color: '#8B5CF6',
                    fontSize: '0.625rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}
                >
                  {layer.status}
                </motion.div>
              </div>
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '1rem'
              }}>
                <span style={{
                  color: '#64748B',
                  fontSize: '0.75rem'
                }}>
                  Connections
                </span>
                <span style={{
                  color: '#8B5CF6',
                  fontSize: '1.125rem',
                  fontWeight: 700
                }}>
                  {layer.connections.toLocaleString()}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          className="performance-metrics"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.3 }}
          style={{
            background: 'rgba(17, 24, 39, 0.6)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(139, 92, 246, 0.2)',
            borderRadius: '1rem',
            padding: '2rem',
            marginBottom: '4rem'
          }}
        >
          <h4 style={{
            color: '#FFFFFF',
            fontSize: '1.25rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
            textAlign: 'center'
          }}>
            System Performance
          </h4>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '2rem'
          }}>
            {[
              { metric: 'Uptime', value: '99.99%', trend: 'up' },
              { metric: 'Latency', value: '0.3ms', trend: 'down' },
              { metric: 'Throughput', value: '1.2TB/s', trend: 'up' },
              { metric: 'Accuracy', value: '99.7%', trend: 'up' }
            ].map((stat, i) => (
              <motion.div
                key={stat.metric}
                className="stat-item"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.5 + i * 0.1 }}
                style={{ textAlign: 'center' }}
              >
                <div style={{
                  color: '#FFFFFF',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  marginBottom: '0.5rem'
                }}>
                  {stat.value}
                </div>
                <div style={{
                  color: '#64748B',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}>
                  {stat.metric}
                  <motion.div
                    animate={{
                      y: stat.trend === 'up' ? [-2, 2, -2] : [2, -2, 2]
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      delay: i * 0.2
                    }}
                    style={{
                      color: stat.trend === 'up' ? '#10B981' : '#EF4444',
                      fontSize: '0.75rem'
                    }}
                  >
                    {stat.trend === 'up' ? '↑' : '↓'}
                  </motion.div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* CTA Section */}
        <motion.div
          className="os-cta"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.7 }}
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
            onClick={handleSystemClick}
            {...createFloatingMotion(0.6)}
          >
            Initialize Neural System
          </CinematicButton>
          
          <motion.div
            className="system-status"
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
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{
                duration: 2,
                repeat: Infinity
              }}
              style={{
                width: '8px',
                height: '8px',
                background: '#10B981',
                borderRadius: '50%'
              }}
            />
            <span>Neural Core Online • All Systems Operational</span>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Neural Network Visualization */}
      <div className="neural-network">
        {Array.from({ length: 20 }, (_, i) => (
          <motion.div
            key={`neural-${i}`}
            className="neural-node"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 0.6, scale: 1 }}
            transition={{
              duration: 1,
              delay: 2 + i * 0.05
            }}
            style={{
              position: 'absolute',
              top: `${10 + Math.random() * 80}%`,
              left: `${10 + Math.random() * 80}%`,
              width: '4px',
              height: '4px',
              background: '#8B5CF6',
              borderRadius: '50%',
              filter: 'blur(1px)',
              pointerEvents: 'none'
            }}
          />
        ))}
        
        {/* Neural Connections */}
        {Array.from({ length: 15 }, (_, i) => (
          <motion.div
            key={`connection-${i}`}
            className="neural-connection"
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{ opacity: 0.2, scaleX: 1 }}
            transition={{
              duration: 1.5,
              delay: 2.5 + i * 0.1
            }}
            style={{
              position: 'absolute',
              top: `${20 + Math.random() * 60}%`,
              left: `${20 + Math.random() * 60}%`,
              width: `${50 + Math.random() * 100}px`,
              height: '1px',
              background: 'linear-gradient(90deg, transparent, #8B5CF6, transparent)',
              transform: `rotate(${Math.random() * 360}deg)`,
              transformOrigin: 'left center',
              pointerEvents: 'none'
            }}
          />
        ))}
      </div>
    </motion.section>
  );
};
