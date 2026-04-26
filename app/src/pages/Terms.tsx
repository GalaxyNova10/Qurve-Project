import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Terms() {
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
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Terms of Service</h1>
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
            <h2 className="text-xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              By accessing or using QUBO Optimizer (&quot;the Service&quot;), you agree to be bound by these Terms of Service. 
              If you disagree with any part of the terms, you may not access the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">2. Description of Service</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              QUBO Optimizer provides quantum-inspired portfolio optimization tools for Indian equity markets (NIFTY 50). 
              The Service includes GPU-accelerated QUBO solvers, Bi-LSTM forecasting, and risk analytics. 
              All calculations and recommendations are for informational purposes only and do not constitute financial advice.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">3. User Accounts</h2>
            <p className="text-[#94A3B8] leading-relaxed mb-4">
              When you create an account with us, you must provide accurate, complete, and current information. 
              Failure to do so constitutes a breach of the Terms, which may result in immediate termination of your account.
            </p>
            <p className="text-[#94A3B8] leading-relaxed">
              You are responsible for safeguarding the password and for all activities that occur under your account. 
              You agree to notify us immediately of any unauthorized use of your account.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">4. Subscription and Payments</h2>
            <p className="text-[#94A3B8] leading-relaxed mb-4">
              Some parts of the Service are billed on a subscription basis. You will be billed in advance on a recurring 
              and periodic basis (monthly or annually), depending on the subscription plan you select.
            </p>
            <p className="text-[#94A3B8] leading-relaxed">
              All fees are exclusive of applicable taxes. You are responsible for paying all taxes associated with your use of the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">5. Disclaimer of Warranties</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              The Service is provided on an &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; basis. QUBO Optimizer makes no warranties, 
              expressed or implied, regarding the accuracy, reliability, or suitability of the Service for any purpose. 
              Past performance is not indicative of future results.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">6. Limitation of Liability</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              In no event shall QUBO Optimizer be liable for any indirect, incidental, special, consequential, or punitive 
              damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, 
              resulting from your access to or use of the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">7. Governing Law</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              These Terms shall be governed and construed in accordance with the laws of India, without regard to 
              its conflict of law provisions. Any disputes arising under these Terms shall be subject to the 
              exclusive jurisdiction of the courts in Mumbai, India.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">8. Contact Us</h2>
            <p className="text-[#94A3B8] leading-relaxed">
              If you have any questions about these Terms, please contact us at{' '}
              <a href="mailto:legal@qubo.ai" className="text-[#FF6200] hover:underline">legal@qubo.ai</a>.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  );
}
