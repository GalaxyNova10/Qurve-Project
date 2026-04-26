import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, ArrowRight, Check, Github, Chrome } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Full name is required';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!agreeTerms) {
      newErrors.terms = 'You must agree to the terms';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      await register(formData.name, formData.email, formData.password);
      navigate('/dashboard');
    } catch (error) {
      // Error handled in auth context
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['#EF4444', '#F59E0B', '#10B981', '#0048B4'];

  const strength = passwordStrength(formData.password);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
        <p className="text-[#94A3B8]">Start optimizing your portfolio today</p>
      </div>

      {/* Social Sign Up */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[#111827] border border-[#1E293B] text-white hover:border-[#FF6200]/50 transition-colors">
          <Chrome className="w-5 h-5" />
          <span className="text-sm">Google</span>
        </button>
        <button className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[#111827] border border-[#1E293B] text-white hover:border-[#FF6200]/50 transition-colors">
          <Github className="w-5 h-5" />
          <span className="text-sm">GitHub</span>
        </button>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 h-px bg-[#1E293B]" />
        <span className="text-[#64748B] text-sm">or sign up with email</span>
        <div className="flex-1 h-px bg-[#1E293B]" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label htmlFor="fullName" className="block text-sm font-medium text-white mb-2">
            Full Name <span className="text-[#EF4444]">*</span>
          </label>
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748B]" aria-hidden="true" />
            <input
              id="fullName"
              name="fullName"
              type="text"
              autoComplete="name"
              required
              aria-required="true"
              aria-invalid={errors.name ? 'true' : 'false'}
              aria-describedby={errors.name ? 'name-error' : undefined}
              value={formData.name}
              onChange={(e) => {
                setFormData({ ...formData, name: e.target.value });
                if (errors.name) setErrors({ ...errors, name: undefined });
              }}
              placeholder="Enter your full name"
              className={`w-full pl-12 pr-4 py-3 bg-[#111827] border rounded-xl text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors ${
                errors.name ? 'border-[#EF4444]' : 'border-[#1E293B]'
              }`}
            />
          </div>
          {errors.name && <p id="name-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.name}</p>}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
            Email Address <span className="text-[#EF4444]">*</span>
          </label>
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748B]" aria-hidden="true" />
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              aria-required="true"
              aria-invalid={errors.email ? 'true' : 'false'}
              aria-describedby={errors.email ? 'email-error' : undefined}
              value={formData.email}
              onChange={(e) => {
                setFormData({ ...formData, email: e.target.value });
                if (errors.email) setErrors({ ...errors, email: undefined });
              }}
              placeholder="Enter your email address"
              className={`w-full pl-12 pr-4 py-3 bg-[#111827] border rounded-xl text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors ${
                errors.email ? 'border-[#EF4444]' : 'border-[#1E293B]'
              }`}
            />
          </div>
          {errors.email && <p id="email-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.email}</p>}
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
              autoComplete="new-password"
              required
              aria-required="true"
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'password-error' : 'password-hint'}
              value={formData.password}
              onChange={(e) => {
                setFormData({ ...formData, password: e.target.value });
                if (errors.password) setErrors({ ...errors, password: undefined });
              }}
              placeholder="Create a strong password (min 8 chars)"
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
          
          {/* Password Strength */}
          {formData.password && (
            <div className="mt-2">
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 h-1.5 bg-[#1E293B] rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(strength / 4) * 100}%`,
                      backgroundColor: strengthColors[strength - 1] || '#1E293B'
                    }}
                  />
                </div>
                <span className="text-xs" style={{ color: strengthColors[strength - 1] || '#64748B' }}>
                  {strengthLabels[strength - 1] || 'Too short'}
                </span>
              </div>
            </div>
          )}
          
          <p id="password-hint" className="mt-1 text-[#64748B] text-xs">Must be at least 8 characters with uppercase, number, and special character</p>
          {errors.password && <p id="password-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.password}</p>}
        </div>

        {/* Confirm Password */}
        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-white mb-2">
            Confirm Password <span className="text-[#EF4444]">*</span>
          </label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748B]" aria-hidden="true" />
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              required
              aria-required="true"
              aria-invalid={errors.confirmPassword ? 'true' : 'false'}
              aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
              value={formData.confirmPassword}
              onChange={(e) => {
                setFormData({ ...formData, confirmPassword: e.target.value });
                if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: undefined });
              }}
              placeholder="Re-enter your password"
              className={`w-full pl-12 pr-4 py-3 bg-[#111827] border rounded-xl text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors ${
                errors.confirmPassword ? 'border-[#EF4444]' : 'border-[#1E293B]'
              }`}
            />
          </div>
          {errors.confirmPassword && (
            <p id="confirm-password-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.confirmPassword}</p>
          )}
        </div>

        {/* Terms */}
        <div>
          <label htmlFor="agree-terms" className="flex items-start gap-3 cursor-pointer">
            <input
              id="agree-terms"
              name="agree-terms"
              type="checkbox"
              checked={agreeTerms}
              onChange={(e) => {
                setAgreeTerms(e.target.checked);
                if (errors.terms) setErrors({ ...errors, terms: undefined });
              }}
              aria-required="true"
              aria-invalid={errors.terms ? 'true' : 'false'}
              aria-describedby={errors.terms ? 'terms-error' : undefined}
              className="mt-1 w-4 h-4 rounded border-[#1E293B] bg-[#111827] text-[#FF6200] focus:ring-[#FF6200]/50"
            />
            <span className="text-[#94A3B8] text-sm">
              I agree to the{' '}
              <Link to="/terms" className="text-[#FF6200] hover:underline">Terms of Service</Link>
              {' '}and{' '}
              <Link to="/privacy" className="text-[#FF6200] hover:underline">Privacy Policy</Link>
              <span className="text-[#EF4444]">*</span>
            </span>
          </label>
          {errors.terms && <p id="terms-error" className="mt-1 text-[#EF4444] text-sm" role="alert">{errors.terms}</p>}
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white hover:opacity-90 py-3 h-12"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              Create Account
              <ArrowRight className="w-4 h-4 ml-2" />
            </>
          )}
        </Button>
      </form>

      {/* Sign In Link */}
      <p className="mt-6 text-center text-[#94A3B8]">
        Already have an account?{' '}
        <Link to="/login" className="text-[#FF6200] hover:underline font-medium">
          Sign in
        </Link>
      </p>

      {/* Features */}
      <div className="mt-6 grid grid-cols-2 gap-3">
        {[
          '14-day free trial',
          'No credit card required',
          'Full API access',
          'Cancel anytime',
        ].map((feature, i) => (
          <div key={i} className="flex items-center gap-2 text-[#94A3B8] text-xs">
            <Check className="w-4 h-4 text-[#10B981]" />
            <span>{feature}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
