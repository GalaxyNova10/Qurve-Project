import { useState } from 'react';
import { motion } from 'framer-motion';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

export default function Register() {
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  return (
    <div className="min-h-screen relative flex items-center justify-center">
      {/* Atmospheric background */}
      <div 
        className="absolute inset-0 transition-all duration-1000"
        style={{
          background: `
            radial-gradient(ellipse at 50% 50%, hsla(${atmosphereHue + 80}, 40%, 6%, ${0.02 + glowIntensity * 0.01}) 0%, transparent 50%),
            linear-gradient(180deg, #050816 0%, #0a0f1e 100%)
          `
        }}
      />

      <div className="relative z-10 w-full max-w-md mx-auto p-4 sm:p-6 lg:p-8">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          className="backdrop-blur-md bg-black/20 rounded-2xl border border-white/10 p-6 sm:p-8"
        >
          {/* Register Header */}
          <div className="text-center mb-8">
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.2 }}
              className="text-3xl font-black leading-tight mb-2"
              style={{
                background: `linear-gradient(135deg, 
                  hsla(${atmosphereHue + 60}, 70%, 55%, 1) 0%, 
                  hsla(${atmosphereHue + 90}, 60%, 45%, 1) 100%
                )`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              Create Account
            </motion.h2>
            <motion.p 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.3 }}
              className="text-gray-400"
            >
              Join the institutional revolution in portfolio intelligence
            </motion.p>
          </div>

          {/* Register Form */}
          <form className="space-y-8">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-3 tracking-wide">
                Full Name
              </label>
              <motion.input
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.4 }}
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
                className="w-full px-4 py-4 bg-black/40 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 backdrop-blur-sm transition-all duration-300"
                style={{
                  boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.1)`
                }}
                placeholder="Enter your full name"
                whileFocus={{
                  scale: 1.01,
                  boxShadow: `0 0 ${30 + glowIntensity * 12}px hsla(${atmosphereHue + 60}, 70%, 50%, 0.2)`
                }}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-3 tracking-wide">
                Email Address
              </label>
              <motion.input
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.5 }}
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                className="w-full px-4 py-4 bg-black/40 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 backdrop-blur-sm transition-all duration-300"
                style={{
                  boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.1)`
                }}
                placeholder="Enter your email"
                whileFocus={{
                  scale: 1.01,
                  boxShadow: `0 0 ${30 + glowIntensity * 12}px hsla(${atmosphereHue + 60}, 70%, 50%, 0.2)`
                }}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-3 tracking-wide">
                Password
              </label>
              <motion.input
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.6 }}
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                className="w-full px-4 py-4 bg-black/40 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 backdrop-blur-sm transition-all duration-300"
                style={{
                  boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.1)`
                }}
                placeholder="Enter your password"
                whileFocus={{
                  scale: 1.01,
                  boxShadow: `0 0 ${30 + glowIntensity * 12}px hsla(${atmosphereHue + 60}, 70%, 50%, 0.2)`
                }}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-3 tracking-wide">
                Confirm Password
              </label>
              <motion.input
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.7 }}
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                required
                className="w-full px-4 py-4 bg-black/40 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 backdrop-blur-sm transition-all duration-300"
                style={{
                  boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 30%, 0.1)`
                }}
                placeholder="Confirm your password"
                whileFocus={{
                  scale: 1.01,
                  boxShadow: `0 0 ${30 + glowIntensity * 12}px hsla(${atmosphereHue + 60}, 70%, 50%, 0.2)`
                }}
              />
            </div>

            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.8 }}
              type="submit"
              className="w-full py-4 px-4 text-white font-bold rounded-xl transition-all duration-300 text-lg"
              style={{
                background: `linear-gradient(135deg, 
                  hsla(${atmosphereHue + 50}, 65%, 55%, 1) 0%, 
                  hsla(${atmosphereHue + 80}, 55%, 45%, 1) 100%
                )`,
                boxShadow: `0 0 ${30 + glowIntensity * 15}px hsla(${atmosphereHue + 60}, 65%, 55%, 0.4)`
              }}
              whileHover={{
                scale: 1.02,
                boxShadow: `0 0 ${40 + glowIntensity * 20}px hsla(${atmosphereHue + 60}, 75%, 60%, 0.5)`
              }}
              whileTap={{ scale: 0.98 }}
            >
              Create Account
            </motion.button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 1 }}
              className="text-gray-400 text-sm"
            >
              Already have an account?{' '}
              <motion.a
                href="/login"
                className="text-purple-400 hover:text-purple-300 font-medium"
                whileHover={{ scale: 1.05 }}
              >
                Sign In
              </motion.a>
            </motion.p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
