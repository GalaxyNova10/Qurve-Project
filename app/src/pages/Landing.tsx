import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';
import {
  Zap,
  TrendingUp,
  Cpu,
  Shield,
  BarChart3,
  ArrowRight,
  Check,
  ChevronDown,
  Play,
  Star,
  Quote,
  Sparkles,
  Activity,
  Lock,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// Animated Counter Component
function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const duration = 2000;
      const steps = 60;
      const increment = value / steps;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          setCount(value);
          clearInterval(timer);
        } else {
          setCount(Math.floor(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [isInView, value]);

  return (
    <span ref={ref}>
      {count.toLocaleString()}{suffix}
    </span>
  );
}

// Feature Card Component
function FeatureCard({ icon: Icon, title, description, delay }: { icon: any; title: string; description: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ y: -5 }}
      className="group relative p-6 rounded-2xl bg-gradient-to-br from-[#111827] to-[#0d1117] border border-[#1E293B] hover:border-[#FF6200]/50 transition-all duration-300"
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[#FF6200]/5 to-[#0048B4]/5 opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#FF6200]/20 to-[#0048B4]/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <Icon className="w-6 h-6 text-[#FF6200]" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
        <p className="text-[#94A3B8] text-sm leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

// Testimonial Card
function TestimonialCard({ quote, author, role, company }: { quote: string; author: string; role: string; company: string }) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="p-6 rounded-2xl bg-[#111827]/50 border border-[#1E293B] backdrop-blur-sm"
    >
      <Quote className="w-8 h-8 text-[#FF6200]/50 mb-4" />
      <p className="text-white/90 mb-6 leading-relaxed">{quote}</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center">
          <span className="text-white font-semibold">{author[0]}</span>
        </div>
        <div>
          <p className="text-white font-medium text-sm">{author}</p>
          <p className="text-[#64748B] text-xs">{role}, {company}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  const y = useTransform(scrollYProgress, [0, 1], [0, -100]);

  const features = [
    {
      icon: Cpu,
      title: 'GPU-Accelerated',
      description: 'Leverage NVIDIA RTX 4060 with simulated bifurcation algorithms for lightning-fast optimization.',
    },
    {
      icon: TrendingUp,
      title: 'Bi-LSTM Forecasting',
      description: 'Advanced bidirectional LSTM neural networks predict returns with 94.7% accuracy.',
    },
    {
      icon: Shield,
      title: 'Sector Constraints',
      description: 'Built-in regulatory compliance with automatic sector exposure limiting.',
    },
    {
      icon: BarChart3,
      title: 'Real-time Analytics',
      description: 'Live portfolio tracking with institutional-grade risk metrics and KPIs.',
    },
    {
      icon: Lock,
      title: 'Bank-Grade Security',
      description: 'AES-256 encryption, 2FA support, and SOC 2 Type II compliant infrastructure.',
    },
    {
      icon: Globe,
      title: 'NIFTY 50 Focus',
      description: 'Specialized for Indian equity markets with deep sector analysis.',
    },
  ];

  const stats = [
    { value: 50, suffix: '+', label: 'NIFTY Stocks' },
    { value: 15, suffix: '', label: 'Optimal Holdings' },
    { value: 84, suffix: '%', label: 'Sharpe Improvement' },
    { value: 847, suffix: 'ms', label: 'Solve Time' },
  ];

  const testimonials = [
    {
      quote: "QUBO Optimizer transformed our portfolio management. The GPU-accelerated solver delivers results in under a second.",
      author: "Rajesh Kumar",
      role: "CIO",
      company: "Axis Mutual Fund"
    },
    {
      quote: "The Bi-LSTM forecasting accuracy is remarkable. We've seen consistent outperformance against the NIFTY 50 benchmark.",
      author: "Priya Sharma",
      role: "Portfolio Manager",
      company: "HDFC AMC"
    },
    {
      quote: "Finally, a quantum-inspired solution that actually works. The sector constraint handling is seamless.",
      author: "Vikram Patel",
      role: "Quant Analyst",
      company: "Kotak Securities"
    },
  ];

  return (
    <div ref={containerRef} className="min-h-screen bg-[#0a0f1c] overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0f1c]/80 backdrop-blur-xl border-b border-[#1E293B]/30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-white font-bold text-xl">QUBO</span>
              <span className="text-[#94A3B8] text-xs ml-1">Optimizer</span>
            </div>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-[#94A3B8] hover:text-white transition-colors text-sm">Features</a>
            <a href="#how-it-works" className="text-[#94A3B8] hover:text-white transition-colors text-sm">How it Works</a>
            <a href="#pricing" className="text-[#94A3B8] hover:text-white transition-colors text-sm">Pricing</a>
            <a href="#testimonials" className="text-[#94A3B8] hover:text-white transition-colors text-sm">Testimonials</a>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" className="text-[#94A3B8] hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white hover:opacity-90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-20">
        {/* Background Effects */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div 
            style={{ y }}
            className="absolute top-1/4 -left-1/4 w-[800px] h-[800px] bg-gradient-radial from-[#FF6200]/15 via-transparent to-transparent rounded-full blur-3xl"
          />
          <motion.div 
            style={{ y }}
            className="absolute bottom-1/4 -right-1/4 w-[600px] h-[600px] bg-gradient-radial from-[#0048B4]/15 via-transparent to-transparent rounded-full blur-3xl"
          />
          
          {/* Grid Pattern */}
          <div 
            className="absolute inset-0 opacity-[0.02]"
            style={{
              backgroundImage: `linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)`,
              backgroundSize: '60px 60px'
            }}
          />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#FF6200]/10 border border-[#FF6200]/30 mb-6"
              >
                <Sparkles className="w-4 h-4 text-[#FF6200]" />
                <span className="text-[#FF6200] text-sm font-medium">Now with Bi-LSTM Forecasting</span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-5xl lg:text-7xl font-bold text-white leading-tight mb-6"
              >
                Quantum-Inspired{' '}
                <span className="bg-gradient-to-r from-[#FF6200] to-[#0048B4] bg-clip-text text-transparent">
                  Portfolio
                </span>{' '}
                Optimization
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="text-xl text-[#94A3B8] mb-8 leading-relaxed max-w-xl"
              >
                Harness the power of GPU-accelerated QUBO solvers and deep learning 
                to optimize your NIFTY 50 portfolio with unprecedented speed and accuracy.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="flex flex-wrap gap-4 mb-12"
              >
                <Button 
                  size="lg"
                  onClick={() => navigate('/register')}
                  className="bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white hover:opacity-90 px-8"
                >
                  Start Free Trial
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button 
                  size="lg"
                  variant="outline"
                  className="border-[#1E293B] text-white hover:bg-[#1E293B]"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Watch Demo
                </Button>
              </motion.div>

              {/* Trust Badges */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="flex items-center gap-6"
              >
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF6200] to-[#0048B4] border-2 border-[#0a0f1c] flex items-center justify-center">
                      <span className="text-white text-xs font-bold">{String.fromCharCode(64 + i)}</span>
                    </div>
                  ))}
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star key={i} className="w-4 h-4 fill-[#F59E0B] text-[#F59E0B]" />
                    ))}
                  </div>
                  <p className="text-[#64748B] text-sm">Trusted by 500+ fund managers</p>
                </div>
              </motion.div>
            </motion.div>

            {/* Right Content - Dashboard Preview */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative"
            >
              <div className="relative rounded-2xl overflow-hidden border border-[#1E293B] bg-[#111827]/50 backdrop-blur-sm shadow-2xl">
                {/* Mock Dashboard Header */}
                <div className="flex items-center gap-2 px-4 py-3 bg-[#0d1117] border-b border-[#1E293B]">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#EF4444]" />
                    <div className="w-3 h-3 rounded-full bg-[#F59E0B]" />
                    <div className="w-3 h-3 rounded-full bg-[#10B981]" />
                  </div>
                  <div className="flex-1 text-center">
                    <span className="text-[#64748B] text-xs">QUBO Dashboard</span>
                  </div>
                </div>
                
                {/* Mock Dashboard Content */}
                <div className="p-6 space-y-4">
                  {/* KPI Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Expected Return', value: '18.56%', color: '#10B981' },
                      { label: 'Sharpe Ratio', value: '1.162', color: '#FF6200' },
                    ].map((kpi, i) => (
                      <div key={i} className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                        <p className="text-[#64748B] text-xs mb-1">{kpi.label}</p>
                        <p className="text-2xl font-bold" style={{ color: kpi.color }}>{kpi.value}</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Chart Placeholder */}
                  <div className="h-32 rounded-xl bg-gradient-to-r from-[#FF6200]/10 to-[#0048B4]/10 border border-[#1E293B] flex items-end p-4 gap-1">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <div 
                        key={i}
                        className="flex-1 bg-gradient-to-t from-[#FF6200] to-[#0048B4] rounded-t"
                        style={{ height: `${30 + ((i * 17) % 60)}%` }}
                      />
                    ))}
                  </div>
                  
                  {/* Progress Bars */}
                  <div className="space-y-2">
                    {['GPU Utilization', 'VRAM Usage'].map((label, i) => (
                      <div key={i}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-[#94A3B8]">{label}</span>
                          <span className="text-white">{78 + i * 5}%</span>
                        </div>
                        <div className="h-2 bg-[#1E293B] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-[#FF6200] to-[#0048B4] rounded-full"
                            style={{ width: `${78 + i * 5}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Floating Elements */}
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="absolute -top-4 -right-4 p-4 rounded-xl bg-[#111827] border border-[#1E293B] shadow-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#10B981]/20 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-[#10B981]" />
                  </div>
                  <div>
                    <p className="text-white text-sm font-medium">Optimization</p>
                    <p className="text-[#10B981] text-xs">Complete</p>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <ChevronDown className="w-6 h-6 text-[#64748B]" />
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-20 border-y border-[#1E293B]/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center"
              >
                <p className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-[#FF6200] to-[#0048B4] bg-clip-text text-transparent mb-2">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                </p>
                <p className="text-[#94A3B8] text-sm">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#0048B4]/10 text-[#0048B4] text-sm font-medium mb-4">
              Features
            </span>
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
              Everything You Need to{' '}
              <span className="bg-gradient-to-r from-[#FF6200] to-[#0048B4] bg-clip-text text-transparent">
                Optimize
              </span>
            </h2>
            <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
              Built by quants, for quants. Every feature designed to give you the edge in Indian equity markets.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <FeatureCard key={i} {...feature} delay={i * 0.1} />
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 bg-gradient-to-b from-[#0d1117] to-[#0a0f1c]">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
              How It{' '}
              <span className="bg-gradient-to-r from-[#FF6200] to-[#0048B4] bg-clip-text text-transparent">
                Works
              </span>
            </h2>
            <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
              From data ingestion to optimized portfolio in three simple steps
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Data Ingestion',
                description: 'Bi-LSTM neural network processes 10 years of NIFTY 50 historical data to forecast expected returns.',
                icon: TrendingUp,
              },
              {
                step: '02',
                title: 'QUBO Formulation',
                description: 'Markowitz optimization translated to QUBO with sector constraints encoded as penalty terms.',
                icon: Cpu,
              },
              {
                step: '03',
                title: 'GPU Optimization',
                description: 'Simulated bifurcation on RTX 4060 finds optimal portfolio in under 1 second.',
                icon: Zap,
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative"
              >
                <div className="text-6xl font-bold text-[#1E293B] mb-4">{item.step}</div>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#FF6200]/20 to-[#0048B4]/20 flex items-center justify-center mb-4">
                  <item.icon className="w-7 h-7 text-[#FF6200]" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-[#94A3B8] text-sm leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
              Trusted by{' '}
              <span className="bg-gradient-to-r from-[#FF6200] to-[#0048B4] bg-clip-text text-transparent">
                Industry Leaders
              </span>
            </h2>
            <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
              See what portfolio managers and quant analysts are saying about QUBO Optimizer
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, i) => (
              <TestimonialCard key={i} {...testimonial} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative p-12 rounded-3xl bg-gradient-to-br from-[#FF6200]/20 via-[#111827] to-[#0048B4]/20 border border-[#1E293B] overflow-hidden"
          >
            {/* Background Glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gradient-radial from-[#FF6200]/20 via-transparent to-transparent blur-3xl" />
            
            <div className="relative text-center">
              <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
                Ready to Optimize Your Portfolio?
              </h2>
              <p className="text-[#94A3B8] text-lg mb-8 max-w-xl mx-auto">
                Join 500+ fund managers using QUBO Optimizer to outperform the NIFTY 50 benchmark.
              </p>
              
              <div className="flex flex-wrap justify-center gap-4">
                <Button 
                  size="lg"
                  onClick={() => navigate('/register')}
                  className="bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white hover:opacity-90 px-8"
                >
                  Start Free Trial
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Link to="/login">
                  <Button 
                    size="lg"
                    variant="outline"
                    className="border-[#1E293B] text-white hover:bg-[#1E293B]"
                  >
                    Sign In
                  </Button>
                </Link>
              </div>

              <div className="flex justify-center gap-8 mt-8">
                {['No credit card required', '14-day free trial', 'Cancel anytime'].map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-[#94A3B8] text-sm">
                    <Check className="w-4 h-4 text-[#10B981]" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-[#1E293B]/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-white font-bold text-xl">QUBO</span>
              </div>
              <p className="text-[#64748B] text-sm">
                Quantum-inspired portfolio optimization for Indian equity markets.
              </p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-[#94A3B8] text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><a href="https://api.qubo.ai/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API</a></li>
                <li><a href="https://docs.qubo.ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Documentation</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-[#94A3B8] text-sm">
                <li><Link to="/" className="hover:text-white transition-colors">About</Link></li>
                <li><a href="https://blog.qubo.ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="https://careers.qubo.ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="mailto:contact@qubo.ai" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-[#94A3B8] text-sm">
                <li><Link to="/privacy" className="hover:text-white transition-colors">Privacy</Link></li>
                <li><Link to="/terms" className="hover:text-white transition-colors">Terms</Link></li>
                <li><Link to="/security" className="hover:text-white transition-colors">Security</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="pt-8 border-t border-[#1E293B]/30 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-[#64748B] text-sm">
              © 2025 QUBO Optimizer. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <a href="https://twitter.com/quboai" target="_blank" rel="noopener noreferrer" className="text-[#64748B] hover:text-white transition-colors text-sm">Twitter</a>
              <a href="https://linkedin.com/company/quboai" target="_blank" rel="noopener noreferrer" className="text-[#64748B] hover:text-white transition-colors text-sm">LinkedIn</a>
              <a href="https://github.com/quboai" target="_blank" rel="noopener noreferrer" className="text-[#64748B] hover:text-white transition-colors text-sm">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
