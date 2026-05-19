import { PremiumNavigation } from '../components/PremiumNavigation';
import { HeroSection } from '../components/HeroSection';
import { IntelligenceEngineSection } from '../components/IntelligenceEngineSection';
import { HowItWorksSection } from '../components/HowItWorksSection';
import { GPUPowerSection } from '../components/GPUPowerSection';
import { FinalCTASection } from '../components/FinalCTASection';

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#050816]">
      <PremiumNavigation />
      <HeroSection />
      <IntelligenceEngineSection />
      <HowItWorksSection />
      <GPUPowerSection />
      <FinalCTASection />
    </div>
  );
}