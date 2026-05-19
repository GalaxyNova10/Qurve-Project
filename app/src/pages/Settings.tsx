import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings2, 
  Bell, 
  Shield, 
  Palette, 
  Database, 
  Save, 
  Mail, 
  Smartphone,
  Moon,
  Sun,
  Monitor,
  Check,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
// import { toast } from 'sonner';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';

interface SettingSection {
  id: string;
  title: string;
  description: string;
  icon: any;
}

const sections: SettingSection[] = [
  { id: 'general', title: 'General', description: 'Basic application settings', icon: Settings2 },
  { id: 'notifications', title: 'Notifications', description: 'Manage your alerts', icon: Bell },
  { id: 'security', title: 'Security', description: 'Password and 2FA', icon: Shield },
  { id: 'appearance', title: 'Appearance', description: 'Theme and display', icon: Palette },
  { id: 'data', title: 'Data & Privacy', description: 'Export and deletion', icon: Database },
];

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const { user, updateSettings } = useAuth();
  const [activeSection, setActiveSection] = useState('general');
  const [isSaving, setIsSaving] = useState(false);

  // Notification settings
  const [notifications, setNotifications] = useState({
    emailAlerts: user?.settings?.emailAlerts ?? true,
    pushNotifications: user?.settings?.pushNotifications ?? true,
    portfolioUpdates: user?.settings?.portfolioUpdates ?? true,
    optimizationComplete: user?.settings?.optimizationComplete ?? true,
    marketOpen: user?.settings?.marketOpen ?? false,
    weeklyReport: user?.settings?.weeklyReport ?? true,
  });

  // General settings
  const [general, setGeneral] = useState({
    language: user?.settings?.language || 'en',
    timezone: user?.settings?.timezone || 'Asia/Kolkata',
    currency: user?.settings?.currency || 'INR',
    dateFormat: user?.settings?.dateFormat || 'DD/MM/YYYY',
  });

  // Security settings
  const [security, setSecurity] = useState({
    twoFactor: user?.settings?.twoFactor ?? false,
    biometric: user?.settings?.biometric ?? false,
    sessionTimeout: user?.settings?.sessionTimeout || '30',
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateSettings({
        ...general,
        ...notifications,
        ...security
      });
    } catch (e) {
      // Context handles the toast
    } finally {
      setIsSaving(false);
    }
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'general':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Language</label>
                <select 
                  value={general.language}
                  onChange={(e) => setGeneral({ ...general, language: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#7C3AED]/50"
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                  <option value="ta">Tamil</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Timezone</label>
                <select 
                  value={general.timezone}
                  onChange={(e) => setGeneral({ ...general, timezone: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#7C3AED]/50"
                >
                  <option value="Asia/Kolkata">IST (UTC+5:30)</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">EST (UTC-5)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Currency</label>
                <select 
                  value={general.currency}
                  onChange={(e) => setGeneral({ ...general, currency: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#7C3AED]/50"
                >
                  <option value="INR">Indian Rupee (₹)</option>
                  <option value="USD">US Dollar ($)</option>
                  <option value="EUR">Euro (€)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Date Format</label>
                <select 
                  value={general.dateFormat}
                  onChange={(e) => setGeneral({ ...general, dateFormat: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#7C3AED]/50"
                >
                  <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                  <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                </select>
              </div>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            {[
              { key: 'emailAlerts', label: 'Email Alerts', description: 'Receive important updates via email', icon: Mail },
              { key: 'pushNotifications', label: 'Push Notifications', description: 'Browser notifications for real-time alerts', icon: Smartphone },
              { key: 'portfolioUpdates', label: 'Portfolio Updates', description: 'Daily summary of portfolio changes', icon: Bell },
              { key: 'optimizationComplete', label: 'Optimization Complete', description: 'Get notified when QUBO solver finishes', icon: Check },
              { key: 'marketOpen', label: 'Market Open/Close', description: 'Reminders for Indian market hours', icon: Sun },
              { key: 'weeklyReport', label: 'Weekly Report', description: 'Comprehensive weekly performance report', icon: Mail },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#7C3AED]/10 flex items-center justify-center">
                    <item.icon className="w-5 h-5 text-[#7C3AED]" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{item.label}</p>
                    <p className="text-[#64748B] text-sm">{item.description}</p>
                  </div>
                </div>
                <Switch
                  checked={notifications[item.key as keyof typeof notifications]}
                  onCheckedChange={(checked) => 
                    setNotifications({ ...notifications, [item.key]: checked })
                  }
                />
              </div>
            ))}
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#10B981]/10 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-[#10B981]" />
                  </div>
                  <div>
                    <p className="text-white font-medium">Two-Factor Authentication</p>
                    <p className="text-[#64748B] text-sm">Add an extra layer of security</p>
                  </div>
                </div>
                <Switch
                  checked={security.twoFactor}
                  onCheckedChange={(checked) => 
                    setSecurity({ ...security, twoFactor: checked })
                  }
                />
              </div>
              {security.twoFactor && (
                <div className="mt-4 p-4 rounded-lg bg-[#10B981]/10 border border-[#10B981]/30">
                  <p className="text-[#10B981] text-sm flex items-center gap-2">
                    <Check className="w-4 h-4" />
                    2FA is enabled. Your account is more secure.
                  </p>
                </div>
              )}
            </div>

            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#7C3AED]/10 flex items-center justify-center">
                    <Smartphone className="w-5 h-5 text-[#0048B4]" />
                  </div>
                  <div>
                    <p className="text-white font-medium">Biometric Login</p>
                    <p className="text-[#64748B] text-sm">Use fingerprint or face recognition</p>
                  </div>
                </div>
                <Switch
                  checked={security.biometric}
                  onCheckedChange={(checked) => 
                    setSecurity({ ...security, biometric: checked })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Session Timeout</label>
              <select 
                value={security.sessionTimeout}
                onChange={(e) => setSecurity({ ...security, sessionTimeout: e.target.value })}
                className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#7C3AED]/50"
              >
                <option value="15">15 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="120">2 hours</option>
                <option value="never">Never</option>
              </select>
            </div>

            <div className="p-4 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-[#EF4444] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-white font-medium">Danger Zone</p>
                  <p className="text-[#94A3B8] text-sm mb-3">These actions cannot be undone.</p>
                  <Button variant="outline" className="border-[#EF4444] text-[#EF4444] hover:bg-[#EF4444]/10">
                    Delete Account
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );

      case 'appearance':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-white mb-4">Theme</label>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { value: 'light', label: 'Light', icon: Sun },
                  { value: 'dark', label: 'Dark', icon: Moon },
                  { value: 'system', label: 'System', icon: Monitor },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTheme(option.value as any)}
                    className={`p-4 rounded-xl border transition-all ${
                      theme === option.value
                        ? 'border-[#FF6200] bg-[#FF6200]/10'
                        : 'border-[#1E293B] bg-[#0d1117] hover:border-[#FF6200]/50'
                    }`}
                  >
                    <option.icon className={`w-6 h-6 mx-auto mb-2 ${theme === option.value ? 'text-[#FF6200]' : 'text-[#94A3B8]'}`} />
                    <p className={`text-sm ${theme === option.value ? 'text-white' : 'text-[#94A3B8]'}`}>{option.label}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-4">Accent Color</label>
              <div className="flex gap-3">
                {[
                  { color: '#FF6200', name: 'Orange' },
                  { color: '#0048B4', name: 'Blue' },
                  { color: '#10B981', name: 'Green' },
                  { color: '#8B5CF6', name: 'Purple' },
                  { color: '#EC4899', name: 'Pink' },
                ].map(({ color, name }) => (
                  <button
                    key={color}
                    title={`Select ${name} accent color`}
                    aria-label={`Select ${name} accent color`}
                    className="w-10 h-10 rounded-full border-2 border-transparent hover:scale-110 transition-transform focus:outline-none focus:ring-2 focus:ring-white/50"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">Compact Mode</p>
                  <p className="text-[#64748B] text-sm">Reduce spacing for more content</p>
                </div>
                <Switch />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">Animations</p>
                  <p className="text-[#64748B] text-sm">Enable smooth transitions</p>
                </div>
                <Switch defaultChecked />
              </div>
            </div>
          </div>
        );

      case 'data':
        return (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-white font-medium">Export Data</p>
                  <p className="text-[#64748B] text-sm">Download all your portfolio data</p>
                </div>
                <Button variant="outline" className="border-[#1E293B] text-[#94A3B8]">
                  <Database className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-white font-medium">API Access</p>
                  <p className="text-[#64748B] text-sm">Manage API keys for programmatic access</p>
                </div>
                <Button variant="outline" className="border-[#1E293B] text-[#94A3B8]">
                  Manage Keys
                </Button>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-[#EF4444] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-white font-medium">Delete All Data</p>
                  <p className="text-[#94A3B8] text-sm mb-3">This will permanently delete all your portfolio data and cannot be undone.</p>
                  <Button variant="outline" className="border-[#EF4444] text-[#EF4444] hover:bg-[#EF4444]/10">
                    Delete All Data
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-[#94A3B8]">Manage your account and application preferences</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardContent className="p-2">
              <nav className="space-y-1">
                {sections.map((section) => {
                  const Icon = section.icon;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                        activeSection === section.id
                          ? 'bg-gradient-to-r from-[#FF6200]/20 to-[#0048B4]/20 text-white border border-[#FF6200]/30'
                          : 'text-[#94A3B8] hover:bg-[#1E293B]/50 hover:text-white'
                      }`}
                    >
                      <Icon className={`w-5 h-5 ${activeSection === section.id ? 'text-[#FF6200]' : ''}`} />
                      <div>
                        <p className="font-medium text-sm">{section.title}</p>
                        <p className="text-xs text-[#64748B]">{section.description}</p>
                      </div>
                    </button>
                  );
                })}
              </nav>
            </CardContent>
          </Card>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-3"
        >
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white">
                  {sections.find(s => s.id === activeSection)?.title}
                </CardTitle>
                <CardDescription className="text-[#64748B]">
                  {sections.find(s => s.id === activeSection)?.description}
                </CardDescription>
              </div>
              <Button 
                onClick={handleSave}
                disabled={isSaving}
                className="bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white"
              >
                {isSaving ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent>
              {renderSection()}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
