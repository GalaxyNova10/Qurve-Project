import React from 'react';
import { motion } from 'framer-motion';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

interface GPUMetric {
  id: string;
  label: string;
  value: string;
  unit: string;
  color: 'purple' | 'cyan' | 'green' | 'orange';
  size: 'small' | 'medium' | 'large';
}

const gpuMetrics: GPUMetric[] = [
  {
    id: 'compute-power',
    label: 'Compute Power',
    value: '2.4',
    unit: 'PFLOPS',
    color: 'purple',
    size: 'large'
  },
  {
    id: 'memory-bandwidth',
    label: 'Memory Bandwidth',
    value: '1.8',
    unit: 'TB/s',
    color: 'cyan',
    size: 'medium'
  },
  {
    id: 'tensor-cores',
    label: 'Tensor Cores',
    value: '540',
    unit: 'Units',
    color: 'green',
    size: 'small'
  },
  {
    id: 'optimization-speed',
    label: 'Optimization Speed',
    value: '94%',
    unit: 'Accuracy',
    color: 'orange',
    size: 'large'
  }
];

export const GPUPowerSection: React.FC = () => {
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  return (
    <section id="infrastructure" className="min-h-screen relative py-32">
      {/* Dramatic atmospheric background */}
      <div 
        className="absolute inset-0 transition-all duration-1000"
        style={{
          background: `
            radial-gradient(ellipse at 25% 25%, hsla(${atmosphereHue + 60}, 45%, 8%, ${0.05 + glowIntensity * 0.02}) 0%, transparent 50%),
            radial-gradient(ellipse at 75% 75%, hsla(${atmosphereHue + 120}, 35%, 6%, ${0.04 + glowIntensity * 0.01}) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, hsla(${atmosphereHue + 180}, 25%, 4%, ${0.03 + glowIntensity * 0.01}) 0%, transparent 50%),
            linear-gradient(180deg, #050816 0%, #0a0f1e 100%)
          `
        }}
      />

      <div className="relative z-10 container mx-auto px-6 lg:px-12">
        
        {/* Monumental Section Header */}
        <motion.div 
          initial={{ opacity: 0, y: 100 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 2 }}
          className="text-center mb-40"
        >
          <h2 
            className="text-6xl lg:text-7xl xl:text-8xl font-black leading-[0.85] tracking-tight mb-16"
            style={{
              '--gradient-start': `hsla(${atmosphereHue + 60}, 70%, 55%, 1)`,
              '--gradient-mid': `hsla(${atmosphereHue + 100}, 60%, 45%, 1)`,
              '--gradient-end': `hsla(${atmosphereHue + 140}, 50%, 35%, 1)`,
              '--glow-color': `hsla(${atmosphereHue + 85}, 70%, 50%, 0.2)`,
              '--glow-size': `${90 + glowIntensity * 25}px`,
              backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: `0 0 var(--glow-size) var(--glow-color)`
            } as React.CSSProperties}
          >
            GPU Infrastructure
            <span className="block text-3xl lg:text-4xl xl:text-5xl text-gray-500 font-light mt-4">
              Quantum-powered computational excellence
            </span>
          </h2>
          <p className="text-xl lg:text-2xl text-gray-600 max-w-5xl mx-auto leading-relaxed mb-24">
            Our GPU-accelerated infrastructure delivers unprecedented computational power, 
            transforming portfolio optimization from hours to milliseconds.
          </p>
        </motion.div>

        {/* Dramatic Graph System */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 2, delay: 0.6 }}
          className="relative h-[400px] lg:h-[500px] mb-40"
        >
          {/* Graph Background */}
          <div className="absolute inset-0 backdrop-blur-md bg-black/30 rounded-3xl border border-white/15 overflow-hidden"
            style={{
              boxShadow: `0 0 ${60 + glowIntensity * 20}px hsla(${atmosphereHue + 80}, 50%, 30%, 0.3)`
            }}
          >
            {/* Enhanced Grid Lines */}
            <div className="absolute inset-0">
              {[...Array(5)].map((_, i) => (
                <div
                  key={`h-line-${i}`}
                  className="absolute w-full h-px"
                  style={{ 
                    top: `${20 + i * 20}%`,
                    background: `linear-gradient(90deg, 
                      hsla(${atmosphereHue + 40}, 60%, 40%, 0.3) 0%, 
                      hsla(${atmosphereHue + 60}, 50%, 30%, 0.2) 50%,
                      hsla(${atmosphereHue + 40}, 60%, 40%, 0.3) 100%
                    )`
                  }}
                />
              ))}
              {[...Array(5)].map((_, i) => (
                <div
                  key={`v-line-${i}`}
                  className="absolute h-full w-px"
                  style={{ 
                    left: `${20 + i * 20}%`,
                    background: `linear-gradient(180deg, 
                      hsla(${atmosphereHue + 40}, 60%, 40%, 0.3) 0%, 
                      hsla(${atmosphereHue + 60}, 50%, 30%, 0.2) 50%,
                      hsla(${atmosphereHue + 40}, 60%, 40%, 0.3) 100%
                    )`
                  }}
                />
              ))}
            </div>

            {/* Enhanced Performance Curves */}
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
              {/* Glow Effects */}
              <defs>
                <filter id="glow1">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
                <filter id="glow2">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={`hsla(${atmosphereHue + 60}, 80%, 60%, 1)`} />
                  <stop offset="100%" stopColor={`hsla(${atmosphereHue + 100}, 70%, 50%, 1)`} />
                </linearGradient>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={`hsla(${atmosphereHue + 120}, 80%, 60%, 1)`} />
                  <stop offset="100%" stopColor={`hsla(${atmosphereHue + 160}, 70%, 50%, 1)`} />
                </linearGradient>
              </defs>
              
              {/* Primary Performance Curve */}
              <motion.path
                d="M 10,80 Q 30,20 50,40 T 90,10"
                fill="none"
                stroke="url(#gradient1)"
                strokeWidth="2"
                filter="url(#glow1)"
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 2, delay: 0.8 }}
              />
              
              {/* Secondary Performance Curve */}
              <motion.path
                d="M 10,70 Q 40,30 60,50 T 90,20"
                fill="none"
                stroke="url(#gradient2)"
                strokeWidth="1.5"
                filter="url(#glow2)"
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 2, delay: 1 }}
              />
              
              {/* Animated Data Points */}
              {[...Array(5)].map((_, i) => (
                <motion.circle
                  key={`point-${i}`}
                  cx={10 + i * 20}
                  cy={80 - i * 15}
                  r={2}
                  fill={`hsla(${atmosphereHue + 80}, 90%, 70%, 1)`}
                  initial={{ opacity: 0, scale: 0 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.8, 1, 0.8]
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    delay: i * 0.2
                  }}
                />
              ))}
            </svg>
          </div>
        </motion.div>

        {/* Institutional Metrics Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-40">
          {gpuMetrics.map((metric, index) => (
            <motion.div
              key={metric.id}
              initial={{ opacity: 0, scale: 0.8, y: 50 }}
              whileInView={{ opacity: 1, scale: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ 
                duration: 1.5, 
                delay: 1.2 + index * 0.2,
                type: 'spring',
                stiffness: 100,
                damping: 12
              }}
              className="relative backdrop-blur-md bg-black/20 rounded-2xl border border-white/10 p-6 overflow-hidden"
              style={{
                transform: metric.size === 'large' ? 'scale(1.1)' : 'scale(1)'
              }}
            >
              {/* Institutional Glow Background */}
              <div 
                className="absolute inset-0 rounded-2xl"
                style={{
                  background: `radial-gradient(
                    ellipse at center,
                    hsla(${atmosphereHue + (metric.color === 'purple' ? 60 : metric.color === 'cyan' ? 180 : metric.color === 'green' ? 120 : 0)}, 65%, 50%, ${0.06 + glowIntensity * 0.03}) 0%,
                    transparent 100%
                  )`
                }}
              />

              {/* Animated institutional border */}
              <motion.div
                className="absolute inset-0 rounded-2xl border-2"
                style={{
                  borderColor: metric.color === 'purple' ? '#7C3AED' : 
                               metric.color === 'cyan' ? '#06B6D4' : 
                               metric.color === 'green' ? '#10B981' : '#F97316',
                  opacity: 0.15 + glowIntensity * 0.1
                }}
                animate={{
                  scale: [1, 1.01, 1],
                  opacity: [0.15 + glowIntensity * 0.1, 0.25 + glowIntensity * 0.1, 0.15 + glowIntensity * 0.1]
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  repeatType: 'reverse',
                  ease: 'easeInOut'
                }}
              />

              <div className="relative z-10">
                <div className="text-gray-400 text-sm mb-2">{metric.label}</div>
                <div className="flex items-baseline gap-2">
                  <motion.span 
                    initial={{ opacity: 0, scale: 0.5 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ 
                      duration: 1, 
                      delay: 1.4 + index * 0.1,
                      type: 'spring',
                      stiffness: 100
                    }}
                    className="text-3xl lg:text-4xl font-black text-white"
                    style={{
                      '--gradient-start': `hsla(${atmosphereHue + (metric.color === 'purple' ? 60 : metric.color === 'cyan' ? 180 : metric.color === 'green' ? 120 : 0)}, 70%, 55%, 1)`,
                      '--gradient-end': `hsla(${atmosphereHue + (metric.color === 'purple' ? 120 : metric.color === 'cyan' ? 240 : metric.color === 'green' ? 300 : 0)}, 60%, 45%, 1)`,
                      backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text'
                    } as React.CSSProperties}
                  >
                    {metric.value}
                  </motion.span>
                  <span className="text-gray-500 text-lg">{metric.unit}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Dramatic Statement */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 2, delay: 2 }}
          className="text-center max-w-4xl mx-auto"
        >
          <p 
            className="text-2xl lg:text-3xl leading-relaxed"
            style={{
              '--gradient-start': `hsla(${atmosphereHue + 80}, 60%, 50%, 1)`,
              '--gradient-end': `hsla(${atmosphereHue + 120}, 50%, 40%, 1)`,
              backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            } as React.CSSProperties}
          >
            Where computational excellence meets financial sophistication. 
            This is not just optimization—this is evolution.
          </p>
        </motion.div>
      </div>
    </section>
  );
};
