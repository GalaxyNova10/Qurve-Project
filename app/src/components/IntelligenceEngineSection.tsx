import React from 'react';
import { motion } from 'framer-motion';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

export const IntelligenceEngineSection: React.FC = () => {
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  return (
    <section id="intelligence" className="min-h-screen relative py-32">
      {/* Atmospheric background */}
      <div 
        className="absolute inset-0 transition-all duration-1000"
        style={{
          background: `radial-gradient(
            ellipse at 30% 50%,
            hsla(${atmosphereHue + 20}, 60%, 12%, ${0.05 + glowIntensity * 0.03}) 0%,
            transparent 100%
          )`
        }}
      />

      <div className="relative z-10 container mx-auto px-6 lg:px-12">
        
        {/* Section Header */}
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 1.2 }}
          className="text-center mb-32"
        >
          <h2 
            className="text-5xl lg:text-6xl xl:text-7xl font-black leading-tight mb-8"
            style={{
              '--gradient-start': `hsla(${atmosphereHue + 10}, 70%, 55%, 1)`,
              '--gradient-end': `hsla(${atmosphereHue + 40}, 60%, 45%, 1)`,
              backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            } as React.CSSProperties}
          >
            The Intelligence Engine
          </h2>
          <p className="text-xl lg:text-2xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
            AI forecasting meets GPU acceleration. Institutional-grade intelligence reimagined.
          </p>
        </motion.div>

        {/* Alternating Layout 1: Visual Left / Text Right */}
        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 1 }}
          className="grid lg:grid-cols-2 gap-16 lg:gap-32 items-center mb-48"
        >
          {/* Left - Visual */}
          <div className="relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, delay: 0.2 }}
              className="relative h-[500px] lg:h-[600px] backdrop-blur-md bg-black/15 rounded-3xl border border-white/10 overflow-hidden"
            >
              {/* Grid-Based Intelligence Visualization */}
              <div className="absolute inset-0 flex items-center justify-center p-8">
                <div className="w-full h-full max-w-lg max-h-lg">
                  
                  {/* CSS Grid Layout */}
                  <div className="grid grid-cols-3 grid-rows-3 gap-6 h-full aspect-square">
                    
                    {/* Top Node */}
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
                      className="col-start-2 row-start-1 rounded-xl bg-black/30 backdrop-blur-sm border border-white/10 p-4 flex items-center justify-center"
                      style={{ willChange: "transform, opacity" }}
                    >
                      <div className="text-center">
                        <div className="text-2xl lg:text-3xl">🧠</div>
                        <div className="text-xs text-gray-400">Neural</div>
                      </div>
                    </motion.div>
                    
                    {/* Left Node */}
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.65, ease: "easeOut" }}
                      className="col-start-1 row-start-2 rounded-xl bg-black/30 backdrop-blur-sm border border-white/10 p-4 flex items-center justify-center"
                      style={{ willChange: "transform, opacity" }}
                    >
                      <div className="text-center">
                        <div className="text-2xl lg:text-3xl">⚡</div>
                        <div className="text-xs text-gray-400">Speed</div>
                      </div>
                    </motion.div>
                    
                    {/* Central AI Core */}
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
                      className="col-start-2 row-start-2 rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/10 backdrop-blur-sm border border-white/10 flex items-center justify-center"
                      style={{ willChange: "transform, opacity" }}
                    >
                      <div className="text-center">
                        <motion.div
                          animate={{ opacity: [0.7, 1, 0.7] }}
                          transition={{ duration: 2, repeat: Infinity }}
                          className="text-2xl lg:text-3xl font-bold text-white"
                          style={{ willChange: "opacity" }}
                        >
                          AI
                        </motion.div>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                          className="absolute inset-0 rounded-full border-2 border-purple-500/30 border-t-purple-500 border-r-purple-500"
                          style={{ willChange: "transform" }}
                        />
                      </div>
                    </motion.div>
                    
                    {/* Right Node */}
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.8, ease: "easeOut" }}
                      className="col-start-3 row-start-2 rounded-xl bg-black/30 backdrop-blur-sm border border-white/10 p-4 flex items-center justify-center"
                      style={{ willChange: "transform, opacity" }}
                    >
                      <div className="text-center">
                        <div className="text-2xl lg:text-3xl">📊</div>
                        <div className="text-xs text-gray-400">Data</div>
                      </div>
                    </motion.div>
                    
                    {/* Bottom Node */}
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.95, ease: "easeOut" }}
                      className="col-start-2 row-start-3 rounded-xl bg-black/30 backdrop-blur-sm border border-white/10 p-4 flex items-center justify-center"
                      style={{ willChange: "transform, opacity" }}
                    >
                      <div className="text-center">
                        <div className="text-2xl lg:text-3xl">🎯</div>
                        <div className="text-xs text-gray-400">Target</div>
                      </div>
                    </motion.div>
                    
                    {/* Empty corners */}
                    <div className="col-start-1 row-start-1"></div>
                    <div className="col-start-3 row-start-1"></div>
                    <div className="col-start-1 row-start-3"></div>
                    <div className="col-start-3 row-start-3"></div>
                  </div>
                  
                  {/* Performance Metrics */}
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { label: 'Accuracy', value: '94.7%' },
                        { label: 'Speed', value: '2.3ms' },
                        { label: 'Models', value: '12' }
                      ].map((metric, i) => (
                        <motion.div
                          key={metric.label}
                          initial={{ opacity: 0, y: 20 }}
                          whileInView={{ opacity: 1, y: 0 }}
                          viewport={{ once: true }}
                          transition={{ duration: 1, delay: 1.2 + i * 0.1, ease: "easeOut" }}
                          className="text-center p-2 rounded-lg bg-black/20 backdrop-blur-sm border border-white/10"
                          style={{ willChange: "transform, opacity" }}
                        >
                          <div className="text-sm lg:text-base font-bold text-white">{metric.value}</div>
                          <div className="text-xs text-gray-400">{metric.label}</div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Right - Text */}
          <div className="space-y-8 lg:space-y-12 lg:pl-8">
            <h3 className="text-4xl lg:text-5xl font-black leading-tight mb-8">
              AI Forecasting
              <span className="block text-2xl lg:text-3xl text-gray-500 font-light">at Scale</span>
            </h3>
            <p className="text-xl lg:text-2xl text-gray-600 leading-relaxed max-w-lg">
              GPU-accelerated optimization processes thousands of portfolios simultaneously, 
              achieving institutional-grade performance at unprecedented speed and scale.
            </p>
            <div className="space-y-6">
              <div className="flex items-start space-x-4 lg:space-x-6">
                <div className="w-3 h-3 lg:w-4 lg:h-4 rounded-full bg-gradient-to-r from-purple-600 to-purple-500 mt-2 lg:mt-3 shadow-lg shadow-purple-500/25"></div>
                <div>
                  <h4 className="text-white font-semibold text-lg lg:text-xl mb-2">Deep Learning Models</h4>
                  <p className="text-gray-500 text-sm lg:text-base leading-relaxed">Advanced transformer architectures for market prediction</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 lg:space-x-6">
                <div className="w-3 h-3 lg:w-4 lg:h-4 rounded-full bg-gradient-to-r from-cyan-600 to-cyan-500 mt-2 lg:mt-3 shadow-lg shadow-cyan-500/25"></div>
                <div>
                  <h4 className="text-white font-semibold text-lg lg:text-xl mb-2">Real-time Processing</h4>
                  <p className="text-gray-500 text-sm lg:text-base leading-relaxed">Sub-millisecond analysis on GPU-accelerated infrastructure</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 lg:space-x-6">
                <div className="w-3 h-3 lg:w-4 lg:h-4 rounded-full bg-gradient-to-r from-green-600 to-green-500 mt-2 lg:mt-3 shadow-lg shadow-green-500/25"></div>
                <div>
                  <h4 className="text-white font-semibold text-lg lg:text-xl mb-2">Adaptive Learning</h4>
                  <p className="text-gray-500 text-sm lg:text-base leading-relaxed">Continuous improvement through market feedback loops</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
