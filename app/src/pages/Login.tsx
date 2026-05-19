import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, User, Lock, ArrowRight, Github, Chrome } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const from = location.state?.from?.pathname || '/dashboard';

  const validate = () => {
    const newErrors: { email?: string; password?: string } = {};
    
    if (!email) {
      newErrors.email = 'Username or email is required';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (error) {
      // Error handled in auth context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
        <p className="text-[#94A3B8]">Sign in to access your portfolio</p>
      </div>

      {/* Social Login */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[#111827] border border-[#1E293B] text-white hover:border-[#7C3AED]/50 transition-colors">
          <Chrome className="w-5 h-5" />
          <span className="text-sm">Google</span>
        </button>
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[#111827] border border-[#1E293B] text-white hover:border-[#7C3AED]/50 transition-colors">
          <Github className="w-5 h-5" />
          <span className="text-sm">GitHub</span>
        </button>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 h-px bg-[#1E293B]" />
        <span className="text-[#64748B] text-sm">or continue with email</span>
        <div className="flex-1 h-px bg-[#1E293B]" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Username or Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
            Username or Email <span className="text-[#EF4444]">*</span>
          </label>
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748B]" aria-hidden="true" />
            <input
              id="email"
              name="email"
              type="text"
              autoComplete="username"
              required
              aria-required="true"
              aria-invalid={errors.email ? 'true' : 'false'}
              aria-describedby={errors.email ? 'email-error' : undefined}
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errors.email) setErrors({ ...errors, email: undefined });
              }}
              placeholder="Enter username or email"
              className={`w-full pl-12 pr-4 py-3 bg-[#111827] border rounded-xl text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors ${
                errors.email ? 'border-[#EF4444]' : 'border-[#1E293B]'
              }`}
            />
          </div>
          {errors.email && (
            <p id="email-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.email}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
            Password <span className="text-[#EF4444]">*</span>
          </label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748B]" aria-hidden="true" />
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              aria-required="true"
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'password-error' : undefined}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errors.password) setErrors({ ...errors, password: undefined });
              }}
              placeholder="Enter your password (min 6 characters)"
              className={`w-full pl-12 pr-12 py-3 bg-[#111827] border rounded-xl text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors ${
                errors.password ? 'border-[#EF4444]' : 'border-[#1E293B]'
              }`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-white transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
            >
              {showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}
            </button>
          </div>
          {errors.password && (
            <p id="password-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.password}</p>
          )}
        </div>

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between">
          <label htmlFor="remember-me" className="flex items-center gap-2 cursor-pointer">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              aria-label="Remember me on this device"
              className="w-4 h-4 rounded border-[#1E293B] bg-[#111827] text-[#7C3AED] focus:ring-[#7C3AED]/50"
            />
            <span className="text-[#94A3B8] text-sm">Remember me</span>
          </label>
          <Link to="/forgot-password" className="text-[#7C3AED] text-sm hover:underline">
            Forgot password?
          </Link>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-[#7C3AED] to-[#8B5CF6] text-white hover:opacity-90 py-3 h-12"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              Sign In
              <ArrowRight className="w-4 h-4 ml-2" />
            </>
          )}
        </Button>
      </form>

      {/* Sign Up Link */}
      <p className="mt-6 text-center text-[#94A3B8]">
        Don't have an account?{' '}
        <Link to="/register" className="text-[#7C3AED] hover:underline font-medium">
          Create one
        </Link>
      </p>

      {/* Demo Credentials */}
      <div className="mt-6 p-4 rounded-xl bg-[#111827] border border-[#1E293B]">
        <p className="text-[#64748B] text-xs mb-2">Demo Credentials:</p>
        <div className="flex items-center justify-between text-sm">
          <code className="text-[#94A3B8]">demo@qurve.ai</code>
          <code className="text-[#94A3B8]">password123</code>
        </div>
      </div>
    </motion.div>
  );
}
