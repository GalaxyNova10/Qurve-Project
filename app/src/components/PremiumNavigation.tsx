import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useEnvironmentalContinuity } from '../hooks/useEnvironmentalContinuity';

export const PremiumNavigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const { glowIntensity, atmosphereHue } = useEnvironmentalContinuity();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path: string) => location.pathname === path;

  return (
    <motion.nav 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled 
          ? 'backdrop-blur-md bg-black/40 border-b border-white/10' 
          : 'backdrop-blur-sm bg-black/20'
      }`}
      style={{
        boxShadow: scrolled 
          ? `0 4px ${20 + glowIntensity * 10}px hsla(${atmosphereHue + 60}, 40%, 30%, 0.15)`
          : 'none'
      }}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-12">
        <div className="flex items-center justify-between h-16 sm:h-20">
          
          {/* Qurve Wordmark */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="flex items-center"
          >
            <Link 
              to="/"
              className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight"
              style={{
                '--gradient-start': `hsla(${atmosphereHue + 40}, 70%, 55%, 1)`,
                '--gradient-end': `hsla(${atmosphereHue + 80}, 60%, 45%, 1)`,
                '--glow-color': `hsla(${atmosphereHue + 60}, 70%, 50%, 0.2)`,
                '--glow-size': `${30 + glowIntensity * 15}px`,
                backgroundImage: 'linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                textShadow: `0 0 var(--glow-size) var(--glow-color)`
              } as React.CSSProperties}
            >
              Qurve
            </Link>
          </motion.div>

          {/* Navigation Links */}
          <div className="hidden lg:flex items-center space-x-12">
            {[
              { path: '#intelligence', label: 'Intelligence' },
              { path: '#infrastructure', label: 'Infrastructure' },
              { path: '#optimization', label: 'Optimization' },
              { path: '#about', label: 'About' }
            ].map((item, index) => (
              <motion.div
                key={item.path}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.3 + index * 0.1 }}
              >
                <Link
                  to={item.path}
                  onClick={(e) => {
                    e.preventDefault();
                    const element = document.querySelector(item.path);
                    if (element) {
                      const offset = 80; // Account for fixed navbar height
                      const elementPosition = element.getBoundingClientRect().top;
                      const offsetPosition = elementPosition + window.pageYOffset - offset;
                      window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                      });
                    }
                  }}
                  className={`text-sm font-medium transition-all duration-300 px-2 py-1 ${
                    isActive(item.path) 
                      ? 'text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                  style={{
                    color: isActive(item.path) 
                      ? `hsla(${atmosphereHue + 40}, 60%, 60%, 1)`
                      : undefined
                  }}
                >
                  {item.label}
                </Link>
              </motion.div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.8 }}
              onClick={() => navigate('/login')}
              className="px-3 sm:px-4 py-2 text-sm font-medium text-white rounded-lg transition-all duration-300"
              style={{
                background: `linear-gradient(135deg, 
                  hsla(${atmosphereHue + 30}, 50%, 45%, 1) 0%, 
                  hsla(${atmosphereHue + 60}, 50%, 35%, 1) 100%
                )`,
                boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 40}, 50%, 45%, 0.3)`,
                borderRadius: '8px',
                border: 'none'
              }}
              whileHover={{ 
                scale: 1.02,
                boxShadow: `0 0 ${25 + glowIntensity * 10}px hsla(${atmosphereHue + 40}, 60%, 50%, 0.4)`
              }}
            >
              Sign In
            </motion.button>

            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.9 }}
              onClick={() => navigate('/register')}
              className="px-3 sm:px-4 py-2 text-sm font-medium text-white rounded-lg transition-all duration-300"
              style={{
                background: `linear-gradient(135deg, 
                  hsla(${atmosphereHue + 50}, 60%, 50%, 1) 0%, 
                  hsla(${atmosphereHue + 80}, 50%, 40%, 1) 100%
                )`,
                boxShadow: `0 0 ${20 + glowIntensity * 8}px hsla(${atmosphereHue + 60}, 50%, 45%, 0.3)`,
                borderRadius: '8px',
                border: 'none'
              }}
              whileHover={{ 
                scale: 1.02,
                boxShadow: `0 0 ${25 + glowIntensity * 10}px hsla(${atmosphereHue + 60}, 60%, 50%, 0.4)`
              }}
            >
              Create Account
            </motion.button>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};
