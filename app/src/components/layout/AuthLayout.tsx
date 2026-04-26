import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#0a0f1c] relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-radial from-[#FF6200]/10 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-radial from-[#0048B4]/10 via-transparent to-transparent rounded-full blur-3xl" />
        
        {/* Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="p-6">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white text-xl">QUBO</h1>
              <p className="text-xs text-[#94A3B8]">Portfolio Optimizer</p>
            </div>
          </motion.div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex items-center justify-center p-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-md"
          >
            <Outlet />
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="p-6 text-center">
          <p className="text-sm text-[#64748B]">
            Quantum-Inspired Portfolio Optimization for Indian Markets
          </p>
        </footer>
      </div>
    </div>
  );
}
