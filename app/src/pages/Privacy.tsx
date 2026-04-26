import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Privacy() {
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
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#0048B4] to-[#FF6200] flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
              <p className="text-[#94A3B8]">Last updated: March 1, 2025</p>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-[#111827] border border-[#1E293B] rounded-2xl p-8 space-y-8"
        >
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">1. Introduction</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              At QUBO Optimizer, we take your privacy seriously. This Privacy Policy explains how we collect, use, 
              disclose, and safeguard your information when you use our Service. Please read this policy carefully 
              to understand our practices regarding your personal data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">2. Information We Collect</h2>
            <h3 className="text-lg font-medium text-white mb-2">Personal Information</h3>
            <ul className="list-disc list-inside text-[#94A3B8] space-y-2 mb-4">
              <li>Name and email address</li>
              <li>Account credentials</li>
              <li>Payment information (processed securely by our payment providers)</li>
              <li>Profile information you choose to provide</li>
            </ul>
            <h3 className="text-lg font-medium text-white mb-2">Usage Data</h3>
            <ul className="list-disc list-inside text-[#94A3B8] space-y-2">
              <li>Portfolio data and optimization preferences</li>
              <li>IP address and browser information</li>
              <li>Device information and operating system</li>
              <li>Access times and pages viewed</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">3. How We Use Your Information</h2>
            <ul className="list-disc list-inside text-[#94A3B8] space-y-2">
              <li>To provide and maintain our Service</li>
              <li>To notify you about changes to our Service</li>
              <li>To provide customer support</li>
              <li>To gather analysis and improve our Service</li>
              <li>To monitor usage and detect technical issues</li>
              <li>To send you newsletters and marketing communications (with your consent)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">4. Data Security</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              We implement industry-standard security measures to protect your personal information, including:
            </p>
            <ul className="list-disc list-inside text-[#94A3B8] space-y-2 mt-2">
              <li>AES-256 encryption for data at rest</li>
              <li>TLS 1.3 for data in transit</li>
              <li>Regular security audits and penetration testing</li>
              <li>Access controls and authentication mechanisms</li>
              <li>SOC 2 Type II compliant infrastructure</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">5. Data Retention</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              We retain your personal information only for as long as necessary to fulfill the purposes outlined 
              in this Privacy Policy. You may request deletion of your account and associated data at any time 
              by contacting us at <a href="mailto:privacy@qubo.ai" className="text-[#FF6200] hover:underline">privacy@qubo.ai</a>.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">6. Your Rights</h2>
            <p className="text-[#94A3B8] leading-relaxed mb-4">
              Under applicable data protection laws, you have the following rights:
            </p>
            <ul className="list-disc list-inside text-[#94A3B8] space-y-2">
              <li>Right to access your personal data</li>
              <li>Right to rectify inaccurate data</li>
              <li>Right to erasure (&quot;right to be forgotten&quot;)</li>
              <li>Right to restrict processing</li>
              <li>Right to data portability</li>
              <li>Right to object to processing</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">7. Cookies and Tracking</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              We use cookies and similar tracking technologies to track activity on our Service and hold certain 
              information. You can instruct your browser to refuse all cookies or to indicate when a cookie is 
              being sent. However, some parts of our Service may not function properly without cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">8. Third-Party Services</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              We may employ third-party companies and individuals to facilitate our Service, provide the Service 
              on our behalf, or assist us in analyzing how our Service is used. These third parties have access 
              to your personal information only to perform these tasks on our behalf and are obligated not to 
              disclose or use it for any other purpose.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">9. Changes to This Policy</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting 
              the new Privacy Policy on this page and updating the &quot;Last updated&quot; date. You are advised to 
              review this Privacy Policy periodically for any changes.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">10. Contact Us</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              If you have any questions about this Privacy Policy, please contact us at{' '}
              <a href="mailto:privacy@qubo.ai" className="text-[#FF6200] hover:underline">privacy@qubo.ai</a>.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  );
}
