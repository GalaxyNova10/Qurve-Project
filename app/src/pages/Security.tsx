import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Lock, CheckCircle, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Security() {
  return (
    <div className="min-h-screen bg-[#0a0f1c] py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Link to="/">
            <Button variant="ghost" className="text-[#94A3B8] hover:text-white mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#10B981] to-[#0048B4] flex items-center justify-center">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Security</h1>
              <p className="text-[#94A3B8]">How we protect your data</p>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-6"
        >
          {/* Security Overview */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-8">
            <h2 className="text-xl font-semibold text-white mb-4">Security Overview</h2>
            <p className="text-[#94A3B8] leading-relaxed mb-6">
              At QUBO Optimizer, security is our top priority. We employ multiple layers of security measures 
              to ensure your portfolio data and personal information remain protected at all times.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                { label: 'Encryption at Rest', value: 'AES-256', status: 'Active' },
                { label: 'Encryption in Transit', value: 'TLS 1.3', status: 'Active' },
                { label: 'Authentication', value: 'JWT + 2FA', status: 'Active' },
                { label: 'Infrastructure', value: 'SOC 2 Type II', status: 'Certified' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between p-4 bg-[#0d1117] rounded-xl">
                  <div>
                    <p className="text-[#64748B] text-sm">{item.label}</p>
                    <p className="text-white font-medium">{item.value}</p>
                  </div>
                  <div className="flex items-center gap-2 text-[#10B981]">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">{item.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Security Features */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-8">
            <h2 className="text-xl font-semibold text-white mb-6">Security Features</h2>
            <div className="space-y-6">
              {[
                {
                  title: 'Two-Factor Authentication (2FA)',
                  description: 'Add an extra layer of security to your account by enabling 2FA. We support authenticator apps and SMS verification.',
                },
                {
                  title: 'Biometric Login',
                  description: 'Use fingerprint or face recognition for quick and secure access to your account on supported devices.',
                },
                {
                  title: 'Session Management',
                  description: 'Control your active sessions and remotely log out from any device. Sessions automatically expire after periods of inactivity.',
                },
                {
                  title: 'API Key Management',
                  description: 'Generate and manage API keys with granular permissions. All API access is logged and monitored.',
                },
              ].map((feature) => (
                <div key={feature.title} className="border-b border-[#1E293B] last:border-0 pb-6 last:pb-0">
                  <h3 className="text-white font-medium mb-2">{feature.title}</h3>
                  <p className="text-[#94A3B8] text-sm">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Best Practices */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-8">
            <h2 className="text-xl font-semibold text-white mb-6">Security Best Practices</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'Use a strong, unique password',
                'Enable two-factor authentication',
                'Keep your devices updated',
                'Be cautious of phishing attempts',
                'Regularly review account activity',
                'Log out from shared devices',
              ].map((practice, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-[#0d1117] rounded-lg">
                  <CheckCircle className="w-5 h-5 text-[#10B981] flex-shrink-0" />
                  <span className="text-[#94A3B8] text-sm">{practice}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reporting */}
          <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-2xl p-8">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-[#EF4444] flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Report a Security Issue</h2>
                <p className="text-[#94A3B8] leading-relaxed mb-4">
                  If you discover a security vulnerability or have concerns about the security of our platform, 
                  please report it immediately to our security team. We take all reports seriously and will 
                  respond promptly.
                </p>
                <a 
                  href="mailto:security@qubo.ai" 
                  className="inline-flex items-center gap-2 text-[#FF6200] hover:underline"
                >
                  Contact Security Team
                </a>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
