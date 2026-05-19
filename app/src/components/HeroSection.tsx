import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

export const HeroSection: React.FC = () => {
  const navigate = useNavigate();
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  return (
    <section className="min-h-screen relative py-12 sm:py-16 lg:py-32 overflow-hidden">
      {/* Static background for immediate render */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(180deg, #050816 0%, #0a0f1e 100%)'
        }}
      />
      
      {/* Animated atmospheric overlay */}
      <div 
        className="absolute inset-0 transition-opacity duration-1000"
        style={{
          background: `
            radial-gradient(ellipse at 20% 30%, hsla(${atmosphereHue + 40}, 50%, 8%, ${0.03 + glowIntensity * 0.01}) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 70%, hsla(${atmosphereHue + 80}, 40%, 6%, ${0.02 + glowIntensity * 0.008}) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, hsla(${atmosphereHue + 120}, 30%, 4%, ${0.01 + glowIntensity * 0.005}) 0%, transparent 50%)
          `
        }}
      />

      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-12">
        <div className="grid lg:grid-cols-2 gap-6 lg:gap-16 items-center min-h-screen">
          
          {/* Left - Hero Content */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1.5 }}
            className="space-y-6 lg:space-y-12"
          >
            <motion.h1 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.2 }}
              className="text-5xl sm:text-6xl lg:text-8xl xl:text-9xl font-black leading-[0.75] tracking-tight"
              style={{
                '--gradient-start': `hsla(${atmosphereHue + 20}, 75%, 60%, 1)`,
                '--gradient-mid': `hsla(${atmosphereHue + 50}, 65%, 50%, 1)`,
                '--gradient-end': `hsla(${atmosphereHue + 80}, 55%, 40%, 1)`,
                '--glow-color': `hsla(${atmosphereHue + 50}, 75%, 55%, 0.2)`,
                '--glow-size': `${80 + glowIntensity * 25}px`,
                backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                textShadow: `0 0 var(--glow-size) var(--glow-color)`
              } as React.CSSProperties}
            >
              Institutional-Grade
              <span className="block text-3xl sm:text-4xl lg:text-5xl xl:text-6xl text-gray-400 font-light mt-3">
                Portfolio Intelligence
              </span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.4 }}
              className="text-lg sm:text-xl lg:text-2xl text-gray-300 max-w-xl sm:max-w-2xl leading-relaxed"
              style={{
                lineHeight: 1.6,
                letterSpacing: '0.01em'
              }}
            >
              Experience the convergence of quantum-inspired algorithms and GPU-accelerated computing 
              delivering unprecedented portfolio optimization at institutional scale.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 sm:gap-6 lg:gap-8 items-start sm:items-center"
            >
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/register')}
                className="relative px-6 sm:px-8 py-4 lg:px-16 lg:py-6 text-lg sm:text-xl lg:text-2xl font-bold text-white rounded-2xl transition-all duration-300 overflow-hidden group h-16 lg:h-20 flex items-center justify-center"
                style={{
                  backgroundImage: `linear-gradient(135deg, 
                    hsla(${atmosphereHue + 40}, 65%, 55%, 1) 0%, 
                    hsla(${atmosphereHue + 70}, 55%, 45%, 1) 100%
                  )`,
                  boxShadow: `0 0 ${40 + glowIntensity * 15}px hsla(${atmosphereHue + 50}, 65%, 55%, 0.4)`
                }}
              >
                <div className="relative z-10">Get Early Access</div>
                <motion.div
                  className="absolute inset-0 rounded-2xl"
                  style={{
                    backgroundImage: `linear-gradient(135deg, 
                      hsla(${atmosphereHue + 60}, 75%, 65%, 1) 0%, 
                      hsla(${atmosphereHue + 90}, 65%, 55%, 1) 100%
                    )`,
                  }}
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/login')}
                className="relative px-6 sm:px-8 py-4 lg:px-16 lg:py-6 text-lg sm:text-xl lg:text-2xl font-bold text-white rounded-2xl transition-all duration-300 overflow-hidden group h-16 lg:h-20 flex items-center justify-center backdrop-blur-sm border border-white/20"
                style={{
                  background: `rgba(255, 255, 255, 0.08)`,
                  boxShadow: `0 0 ${30 + glowIntensity * 10}px hsla(${atmosphereHue + 40}, 60%, 50%, 0.2)`
                }}
              >
                <div className="relative z-10">Sign In</div>
                <motion.div
                  className="absolute inset-0 rounded-2xl"
                  style={{
                    background: `rgba(255, 255, 255, 0.12)`,
                  }}
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                />
              </motion.button>
            </motion.div>
          </motion.div>

          {/* Right - Visual Ecosystem */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 2.0, delay: 0.3, ease: "easeOut" }}
            className="relative h-[500px] lg:h-[600px] motion-safe"
            style={{ 
              willChange: "transform, opacity",
              transform: "translateZ(0)"
            }}
          >
            {/* Primary Dashboard Panel */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ duration: 1.8, delay: 0.4, ease: "easeOut" }}
              className="absolute top-8 right-8 w-64 lg:w-80 h-48 lg:h-56 backdrop-blur-md bg-black/30 rounded-2xl border border-white/10 overflow-hidden motion-safe"
              style={{
                boxShadow: `0 0 ${40 + glowIntensity * 15}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.2)`,
                willChange: "transform, opacity",
                transform: "translateZ(0)"
              }}
            >
              {/* Dashboard Grid */}
              <div className="grid grid-cols-3 gap-2 p-4">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={`grid-${i}`}
                    className="h-8 lg:h-10 bg-gradient-to-br from-purple-500/20 to-blue-500/10 rounded-lg border border-white/5"
                    style={{
                      background: `linear-gradient(135deg, 
                        hsla(${atmosphereHue + (i % 3) * 20}, 60%, 50%, ${0.1 + glowIntensity * 0.05}) 0%, 
                        hsla(${atmosphereHue + (i % 3) * 20 + 40}, 50%, 40%, ${0.05 + glowIntensity * 0.03}) 100%
                      )`,
                      opacity: 0.8 + (i % 2) * 0.2,
                      willChange: "opacity"
                    }}
                  />
                ))}
              </div>
              
              {/* Telemetry Lines */}
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
                <motion.path
                  d="M 10,50 Q 30,20 50,40 T 90,30"
                  fill="none"
                  stroke={`hsla(${atmosphereHue + 80}, 70%, 50%, 0.3)`}
                  strokeWidth="0.5"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.5, delay: 1.2, ease: "easeOut" }}
                />
                <motion.path
                  d="M 10,70 Q 40,40 60,60 T 90,50"
                  fill="none"
                  stroke={`hsla(${atmosphereHue + 120}, 70%, 50%, 0.3)`}
                  strokeWidth="0.5"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.5, delay: 1.4, ease: "easeOut" }}
                />
              </svg>
            </motion.div>

            {/* Floating Analytics Fragment 1 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              animate={{
                y: [0, -8, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
              className="absolute top-32 left-12 w-48 lg:w-56 h-32 lg:h-40 backdrop-blur-sm bg-black/20 rounded-xl border border-white/10 p-4"
              style={{
                boxShadow: `0 0 ${30 + glowIntensity * 10}px hsla(${atmosphereHue + 40}, 50%, 30%, 0.15)`,
                willChange: "transform"
              }}
            >
              <div className="space-y-2">
                <div className="text-xs lg:text-sm text-gray-400">GPU Utilization</div>
                <div className="h-2 bg-gradient-to-r from-green-500/50 to-blue-500/50 rounded-full" />
                <div className="text-xs text-gray-500">94.7%</div>
              </div>
            </motion.div>

            {/* Floating Analytics Fragment 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              animate={{
                y: [0, 6, 0],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 1
              }}
              className="absolute bottom-24 right-16 w-40 lg:w-48 h-28 lg:h-32 backdrop-blur-sm bg-black/20 rounded-xl border border-white/10 p-3"
              style={{
                boxShadow: `0 0 ${25 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.15)`,
                willChange: "transform"
              }}
            >
              <div className="space-y-2">
                <div className="text-xs lg:text-sm text-gray-400">AI Performance</div>
                <div className="grid grid-cols-2 gap-1">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={`perf-${i}`}
                      className="h-4 bg-gradient-to-t from-purple-500/30 to-transparent rounded"
                      style={{ height: `${20 + i * 15}%` }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Central AI Core */}
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, delay: 0.6, ease: "easeOut" }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 lg:w-32 lg:h-32"
              style={{ willChange: "transform, opacity" }}
            >
              <div 
                className="absolute inset-0 rounded-full"
                style={{
                  background: `radial-gradient(circle, 
                    hsla(${atmosphereHue + 50}, 70%, 40%, ${0.4 + glowIntensity * 0.2}) 0%, 
                    hsla(${atmosphereHue + 80}, 60%, 30%, ${0.2 + glowIntensity * 0.2}) 50%,
                    transparent 100%
                  )`,
                  boxShadow: `0 0 ${60 + glowIntensity * 20}px hsla(${atmosphereHue + 60}, 70%, 50%, 0.3)`
                }}
              />
              <motion.div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 lg:w-12 lg:h-12 rounded-full bg-white/10 backdrop-blur-sm"
                animate={{
                  scale: [1, 1.15, 1],
                  opacity: [0.6 + glowIntensity * 0.2, 0.8 + glowIntensity * 0.2, 0.6 + glowIntensity * 0.2]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 0.5
                }}
                style={{ willChange: "transform, opacity" }}
              />
            </motion.div>

            {/* Floating Graph Ribbons */}
            {[...Array(2)].map((_, i) => (
              <motion.div
                key={`ribbon-${i}`}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 0.6 + glowIntensity * 0.2 }}
                viewport={{ once: true }}
                animate={{
                  x: [0, 15, 0],
                  opacity: [0.3 + glowIntensity * 0.1, 0.6 + glowIntensity * 0.2, 0.3 + glowIntensity * 0.1]
                }}
                transition={{
                  duration: 6 + i * 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.5
                }}
                className="absolute"
                style={{
                  width: `${80 + i * 20}px`,
                  height: '2px',
                  left: `${15 + i * 15}%`,
                  top: `${60 + i * 10}%`,
                  background: `linear-gradient(90deg, 
                    hsla(${atmosphereHue + i * 15}, 70%, 50%, ${0.3 + glowIntensity * 0.2}) 0%, 
                    transparent 100%
                  )`,
                  willChange: "transform, opacity",
                  transform: `rotate(${-15 + i * 10}deg)`
                }}
              />
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
};
