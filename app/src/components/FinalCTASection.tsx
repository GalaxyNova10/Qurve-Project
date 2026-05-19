import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

export const FinalCTASection: React.FC = () => {
  const navigate = useNavigate();
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  return (
    <section id="about" className="min-h-screen relative py-32 flex items-center justify-center">
      {/* Monumental atmospheric background with institutional depth */}
      <div 
        className="absolute inset-0 transition-all duration-1000"
        style={{
          background: `
            radial-gradient(ellipse at 25% 30%, hsla(${atmosphereHue + 100}, 40%, 6%, ${0.04 + glowIntensity * 0.02}) 0%, transparent 50%),
            radial-gradient(ellipse at 75% 70%, hsla(${atmosphereHue + 140}, 30%, 4%, ${0.03 + glowIntensity * 0.01}) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, hsla(${atmosphereHue + 180}, 25%, 2%, ${0.02 + glowIntensity * 0.01}) 0%, transparent 50%),
            radial-gradient(ellipse at 25% 80%, hsla(${atmosphereHue + 220}, 20%, 3%, ${0.01 + glowIntensity * 0.005}) 0%, transparent 50%),
            linear-gradient(180deg, #050816 0%, #0a0f1e 100%)
          `
        }}
      />

      {/* Monumental atmospheric lighting effects */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-0 left-1/4 w-96 h-96 rounded-full"
          style={{
            background: `radial-gradient(circle, 
              hsla(${atmosphereHue + 80}, 50%, 20%, ${0.05 + glowIntensity * 0.02}) 0%, 
              transparent 100%
            )`,
          }}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.05 + glowIntensity * 0.02, 0.08 + glowIntensity * 0.03, 0.05 + glowIntensity * 0.02]
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'easeInOut'
          }}
        />
        
        <motion.div
          className="absolute bottom-0 right-1/4 w-96 h-96 rounded-full"
          style={{
            background: `radial-gradient(circle, 
              hsla(${atmosphereHue + 160}, 45%, 15%, ${0.04 + glowIntensity * 0.01}) 0%, 
              transparent 100%
            )`,
          }}
          animate={{
            scale: [1.3, 1, 1.3],
            opacity: [0.04 + glowIntensity * 0.01, 0.06 + glowIntensity * 0.02, 0.04 + glowIntensity * 0.01]
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'easeInOut'
          }}
        />
        
        <motion.div
          className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full"
          style={{
            background: `radial-gradient(circle, 
              hsla(${atmosphereHue + 200}, 35%, 12%, ${0.06 + glowIntensity * 0.03}) 0%, 
              transparent 100%
            )`,
          }}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.06 + glowIntensity * 0.03, 0.1 + glowIntensity * 0.04, 0.06 + glowIntensity * 0.03]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'easeInOut'
          }}
        />
      </div>

      <div className="relative z-10 container mx-auto px-6 lg:px-12">
        
        {/* Monumental Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 2.5, ease: [0.25, 0.1, 0.25, 1] }}
          className="text-center mb-40"
        >
          <motion.h2 
            className="text-7xl lg:text-8xl xl:text-9xl font-black leading-[0.8] tracking-tight mb-16"
            style={{
              '--gradient-start': `hsla(${atmosphereHue + 100}, 70%, 55%, 1)`,
              '--gradient-mid': `hsla(${atmosphereHue + 130}, 60%, 45%, 1)`,
              '--gradient-end': `hsla(${atmosphereHue + 160}, 50%, 35%, 1)`,
              '--glow-color': `hsla(${atmosphereHue + 120}, 70%, 50%, 0.2)`,
              '--glow-size': `${100 + glowIntensity * 30}px`,
              backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: `0 0 var(--glow-size) var(--glow-color)`
            } as React.CSSProperties}
          >
            The Future
            <span className="block text-3xl lg:text-4xl xl:text-5xl text-gray-500 font-light mt-6">
              of Portfolio Intelligence
            </span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 2, delay: 0.8 }}
            className="text-xl lg:text-2xl text-gray-600 max-w-5xl mx-auto leading-relaxed mb-24"
          >
            Join the institutional revolution in portfolio optimization. Experience the convergence 
            of quantum-inspired algorithms and GPU-accelerated computing at unprecedented scale.
          </motion.p>
        </motion.div>
        
        {/* Monumental CTA Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 2, delay: 1.2 }}
          className="max-w-6xl mx-auto"
        >
          <div className="flex flex-col sm:flex-row gap-6 lg:gap-8 items-center justify-center">
            {/* Primary CTA */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/register')}
              className="relative px-8 lg:px-12 py-6 lg:py-8 text-xl font-bold text-white rounded-2xl transition-all duration-500 overflow-hidden group h-20 lg:h-24 flex items-center justify-center flex-1 max-w-md"
              style={{
                background: `linear-gradient(135deg, 
                  hsla(${atmosphereHue + 100}, 65%, 55%, 1) 0%, 
                  hsla(${atmosphereHue + 130}, 55%, 45%, 1) 100%
                )`,
                boxShadow: `0 0 ${60 + glowIntensity * 25}px hsla(${atmosphereHue + 110}, 65%, 55%, 0.4)`
              }}
            >
              <div className="relative z-10 flex items-center justify-center">
                <span className="text-xl lg:text-2xl">Get Early Access</span>
              </div>
              
              {/* Monumental hover effect */}
              <motion.div
                className="absolute inset-0 rounded-2xl"
                style={{
                  background: `linear-gradient(135deg, 
                    hsla(${atmosphereHue + 120}, 75%, 65%, 1) 0%, 
                    hsla(${atmosphereHue + 150}, 65%, 55%, 1) 100%
                  )`,
                }}
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 1 }}
                transition={{ 
                  duration: 0.4,
                  ease: 'easeOut'
                }}
              />
            </motion.button>
            
            {/* Secondary CTA */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/login')}
              className="relative px-8 lg:px-12 py-6 lg:py-8 text-xl font-bold text-white rounded-2xl transition-all duration-500 overflow-hidden group h-20 lg:h-24 flex items-center justify-center flex-1 max-w-md backdrop-blur-sm border border-white/20"
              style={{
                background: `rgba(255, 255, 255, 0.08)`,
                boxShadow: `0 0 ${50 + glowIntensity * 20}px hsla(${atmosphereHue + 90}, 55%, 50%, 0.3)`
              }}
            >
              <div className="relative z-10 flex items-center justify-center">
                <span className="text-xl lg:text-2xl">Sign In</span>
              </div>
              
              {/* Monumental hover effect */}
              <motion.div
                className="absolute inset-0 rounded-2xl"
                style={{
                  background: `rgba(255, 255, 255, 0.12)`,
                }}
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 1 }}
                transition={{ 
                  duration: 0.4,
                  ease: 'easeOut'
                }}
              />
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
