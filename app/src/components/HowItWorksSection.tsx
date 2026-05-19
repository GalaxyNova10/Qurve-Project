import React from 'react';
import { motion } from 'framer-motion';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

interface ProcessStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
}

const processSteps: ProcessStep[] = [
  {
    id: 'data-ingestion',
    title: 'Data Ingestion',
    description: 'Real-time market data streams processed through advanced normalization pipelines',
    icon: '📊',
    color: 'purple'
  },
  {
    id: 'ai-forecasting',
    title: 'AI Forecasting',
    description: 'Deep learning models analyze patterns and predict market movements with 94% accuracy',
    icon: '🤖',
    color: 'cyan'
  },
  {
    id: 'portfolio-rebalancing',
    title: 'Portfolio Rebalancing',
    description: 'GPU-accelerated optimization algorithms rebalance portfolios in milliseconds',
    icon: '⚖️',
    color: 'green'
  },
  {
    id: 'optimization-convergence',
    title: 'Optimization Convergence',
    description: 'Advanced algorithms optimize risk-adjusted returns efficiently',
    icon: '🎯',
    color: 'yellow'
  }
];

export const HowItWorksSection: React.FC = () => {
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  const getColorValue = (color: string) => {
    switch(color) {
      case 'purple': return 60;
      case 'cyan': return 180;
      case 'green': return 120;
      case 'orange': return 0;
      default: return 0;
    }
  };

  
  return (
    <section id="optimization" className="min-h-screen relative py-32">
      {/* Enhanced atmospheric background with institutional depth */}
      <div 
        className="absolute inset-0 transition-all duration-1000"
        style={{
          background: `
            radial-gradient(ellipse at 30% 40%, hsla(${atmosphereHue + 50}, 40%, 8%, ${0.04 + glowIntensity * 0.02}) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 60%, hsla(${atmosphereHue + 100}, 30%, 6%, ${0.03 + glowIntensity * 0.01}) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, hsla(${atmosphereHue + 130}, 25%, 4%, ${0.02 + glowIntensity * 0.01}) 0%, transparent 50%),
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
            className="text-5xl lg:text-6xl xl:text-7xl font-black leading-[0.85] tracking-tight mb-16"
            style={{
              '--gradient-start': `hsla(${atmosphereHue + 50}, 70%, 55%, 1)`,
              '--gradient-mid': `hsla(${atmosphereHue + 90}, 60%, 45%, 1)`,
              '--gradient-end': `hsla(${atmosphereHue + 120}, 50%, 35%, 1)`,
              '--glow-color': `hsla(${atmosphereHue + 85}, 70%, 50%, 0.2)`,
              '--glow-size': `${90 + glowIntensity * 25}px`,
              backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 50%, var(--gradient-end) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: `0 0 var(--glow-size) var(--glow-color)`
            } as React.CSSProperties}
          >
            How It Works
            <span className="block text-2xl lg:text-3xl xl:text-4xl text-gray-500 font-light mt-4">
              Experience the elegance of institutional-grade portfolio intelligence
            </span>
          </h2>
          <p className="text-xl lg:text-2xl text-gray-600 max-w-5xl mx-auto leading-relaxed mb-24">
            Our guided optimization journey transforms complex financial data into actionable insights 
            through a seamless, Apple-quality user experience.
          </p>
        </motion.div>

        {/* Apple-Quality Process Timeline */}
        <div className="relative h-[700px] lg:h-[900px] mb-40">
          
          {/* Enhanced Cinematic Connection Lines */}
          <div className="absolute inset-0 hidden lg:block">
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={`connection-${i}`}
                initial={{ scaleX: 0, opacity: 0 }}
                whileInView={{ scaleX: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ 
                  duration: 2.5, 
                  delay: 0.6 + i * 0.3,
                  ease: 'easeInOut'
                }}
                className="absolute w-full h-1 bg-gradient-to-r from-transparent via-purple-500/40 to-transparent rounded-full"
                style={{
                  transform: `translateY(-50%)`,
                  top: `${25 + i * 25}%`,
                  opacity: 0.4 + glowIntensity * 0.3,
                  background: `linear-gradient(90deg, 
                    transparent 0%, 
                    hsla(${atmosphereHue + 60}, 70%, 50%, ${0.3 + glowIntensity * 0.2}) 50%, 
                    transparent 100%
                  )`
                }}
              />
            ))}
          </div>

          {/* Enhanced Process Steps */}
          <div className="relative h-full flex items-center justify-center px-4 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 lg:gap-8 w-full max-w-7xl">
              {processSteps.map((step, index) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, scale: 0.8, y: 50 }}
                  whileInView={{ opacity: 1, scale: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ 
                    duration: 1.2, 
                    delay: 0.6 + index * 0.15,
                    ease: "easeOut"
                  }}
                  className="relative"
                  style={{ willChange: "transform, opacity" }}
                >
                  
                  {/* Step Container */}
                  <div className="relative backdrop-blur-md bg-black/25 rounded-3xl border border-white/15 p-6 lg:p-8 overflow-hidden w-full"
                    style={{
                      boxShadow: `0 0 ${40 + glowIntensity * 15}px hsla(${atmosphereHue + getColorValue(step.color)}, 50%, 30%, 0.25)`
                    }}
                  >
                                        
                    <div className="relative z-10">
                      {/* Step Number */}
                      <motion.div
                        initial={{ scale: 0, rotate: -180 }}
                        whileInView={{ scale: 1, rotate: 0 }}
                        viewport={{ once: true }}
                        transition={{ 
                          duration: 1, 
                          delay: 0.8 + index * 0.1,
                          ease: "easeOut"
                        }}
                        className="w-16 h-16 lg:w-20 lg:h-20 rounded-full flex items-center justify-center text-lg lg:text-xl font-black mb-4"
                        style={{
                          background: `linear-gradient(135deg, 
                            hsla(${atmosphereHue + getColorValue(step.color)}, 70%, 55%, 1) 0%, 
                            hsla(${atmosphereHue + getColorValue(step.color) + 60}, 60%, 45%, 1) 100%
                          )`,
                          boxShadow: `0 0 ${35 + glowIntensity * 15}px hsla(${atmosphereHue + getColorValue(step.color)}, 75%, 55%, 0.4)`,
                          willChange: "transform, opacity"
                        }}
                      >
                        {index + 1}
                      </motion.div>
                      
                      {/* Step Content */}
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-lg lg:text-xl font-bold text-white mb-2 leading-tight">{step.title}</h3>
                          <p className="text-gray-300 text-sm lg:text-base leading-relaxed">{step.description}</p>
                        </div>
                        
                        {/* Step Icon */}
                        <motion.div
                          initial={{ rotate: -180, opacity: 0 }}
                          whileInView={{ rotate: 0, opacity: 1 }}
                          viewport={{ once: true }}
                          transition={{ 
                            duration: 1, 
                            delay: 1 + index * 0.1,
                            ease: "easeOut"
                          }}
                          className="text-3xl lg:text-4xl"
                          style={{
                            filter: `drop-shadow(0 0 ${20 + glowIntensity * 10}px hsla(${atmosphereHue + getColorValue(step.color)}, 75%, 55%, 0.4))`,
                            willChange: "transform, opacity"
                          }}
                        >
                          {step.icon}
                        </motion.div>
                      </div>
                    </div>
                  </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
    </section>
  );
};
