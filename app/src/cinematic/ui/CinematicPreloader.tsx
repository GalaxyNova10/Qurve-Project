import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Preloader phases
enum PreloaderPhase {
  INITIALIZING = 'initializing',
  BOOTING = 'booting',
  AWAKENING = 'awakening',
  READY = 'ready'
}

// Preloader component with cinematic boot sequence
export const CinematicPreloader: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const [phase, setPhase] = useState<PreloaderPhase>(PreloaderPhase.INITIALIZING);
  const [progress, setProgress] = useState(0);
  const [systemStatus, setSystemStatus] = useState<string[]>([]);

  // Boot sequence timeline
  useEffect(() => {
    const bootSequence = async () => {
      // Phase 1: Initializing
      setPhase(PreloaderPhase.INITIALIZING);
      setSystemStatus(['Initializing Qurve Intelligence Core...']);
      
      await new Promise(resolve => setTimeout(resolve, 800));
      setProgress(15);
      
      // Phase 2: Booting
      setPhase(PreloaderPhase.BOOTING);
      setSystemStatus(prev => [...prev, 'Loading Quantum Algorithms...']);
      
      await new Promise(resolve => setTimeout(resolve, 600));
      setProgress(30);
      setSystemStatus(prev => [...prev, 'Calibrating Neural Networks...']);
      
      await new Promise(resolve => setTimeout(resolve, 700));
      setProgress(50);
      setSystemStatus(prev => [...prev, 'Establishing Atmospheric Connection...']);
      
      // Phase 3: Awakening
      setPhase(PreloaderPhase.AWAKENING);
      setSystemStatus(prev => [...prev, 'Awakening AI Consciousness...']);
      
      await new Promise(resolve => setTimeout(resolve, 800));
      setProgress(75);
      setSystemStatus(prev => [...prev, 'Optimizing Performance Matrix...']);
      
      await new Promise(resolve => setTimeout(resolve, 600));
      setProgress(90);
      setSystemStatus(prev => [...prev, 'Synchronizing Spatial Environment...']);
      
      // Phase 4: Ready
      await new Promise(resolve => setTimeout(resolve, 500));
      setPhase(PreloaderPhase.READY);
      setProgress(100);
      setSystemStatus(prev => [...prev, 'Qurve Intelligence Online']);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      onComplete();
    };

    bootSequence();
  }, [onComplete]);

  return (
    <motion.div
      className="cinematic-preloader"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: '#050816',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Animated background particles */}
      <div className="preloader-particles">
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
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2
            }}
            style={{
              position: 'absolute',
              width: '2px',
              height: '2px',
              background: '#7C3AED',
              borderRadius: '50%',
              filter: 'blur(1px)'
            }}
          />
        ))}
      </div>

      {/* Central content */}
      <motion.div
        className="preloader-content"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        style={{
          textAlign: 'center',
          zIndex: 10
        }}
      >
        {/* Qurve logo with animation */}
        <motion.div
          className="qurve-logo"
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{ duration: 2, ease: "easeInOut", repeat: Infinity, repeatDelay: 1 }}
          style={{
            width: '120px',
            height: '120px',
            margin: '0 auto 40px',
            position: 'relative'
          }}
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              border: '3px solid #7C3AED',
              borderRadius: '50%',
              position: 'relative',
              boxShadow: '0 0 40px rgba(124, 58, 237, 0.5)'
            }}
          >
            {/* Inner rotating ring */}
            <motion.div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: '80%',
                height: '80%',
                border: '2px solid #06B6D4',
                borderRadius: '50%',
                transform: 'translate(-50%, -50%)',
                borderTopColor: 'transparent'
              }}
              animate={{ rotate: 360 }}
              transition={{ duration: 1, ease: "linear", repeat: Infinity }}
            />
            
            {/* Core glow */}
            <motion.div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: '40%',
                height: '40%',
                background: 'radial-gradient(circle, #7C3AED, transparent)',
                borderRadius: '50%',
                transform: 'translate(-50%, -50%)'
              }}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.8, 1, 0.8]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          </div>
        </motion.div>

        {/* System status messages */}
        <div className="system-status" style={{ marginBottom: '30px', minHeight: '120px' }}>
          <AnimatePresence mode="wait">
            {systemStatus.map((status) => (
              <motion.div
                key={status}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                style={{
                  color: '#94A3B8',
                  fontSize: '14px',
                  fontFamily: 'monospace',
                  marginBottom: '8px',
                  textShadow: '0 0 10px rgba(124, 58, 237, 0.5)'
                }}
              >
                {status}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Progress bar */}
        <div className="progress-container" style={{ width: '300px', margin: '0 auto' }}>
          <div
            style={{
              height: '2px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '1px',
              overflow: 'hidden',
              marginBottom: '10px'
            }}
          >
            <motion.div
              className="progress-bar"
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #7C3AED, #06B6D4)',
                borderRadius: '1px',
                boxShadow: '0 0 10px rgba(124, 58, 237, 0.5)'
              }}
            />
          </div>
          
          <div
            style={{
              color: '#64748B',
              fontSize: '12px',
              fontFamily: 'monospace',
              display: 'flex',
              justifyContent: 'space-between'
            }}
          >
            <span>SYSTEM BOOT</span>
            <span>{progress}%</span>
          </div>
        </div>

        {/* Phase indicator */}
        <motion.div
          className="phase-indicator"
          key={phase}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            marginTop: '40px',
            color: '#7C3AED',
            fontSize: '12px',
            fontFamily: 'monospace',
            textTransform: 'uppercase',
            letterSpacing: '2px'
          }}
        >
          {phase}
        </motion.div>
      </motion.div>

      {/* Ambient lighting effects */}
      <div
        className="ambient-lighting"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          background: `
            radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 20% 80%, rgba(6, 182, 212, 0.05) 0%, transparent 50%)
          `,
          mixBlendMode: 'screen'
        }}
      />
    </motion.div>
  );
};

// Hook for managing preloader state
export const usePreloader = () => {
  const [isLoading, setIsLoading] = useState(true);

  const startLoading = () => {
    setIsLoading(true);
  };

  const completeLoading = () => {
    setIsLoading(false);
  };

  return {
    isLoading,
    startLoading,
    completeLoading
  };
};
