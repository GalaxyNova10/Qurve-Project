import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Mail, 
  Phone, 
  Building2, 
  MapPin, 
  Calendar, 
  Camera, 
  Edit2, 
  Check,
  Shield,
  Award,
  TrendingUp,
  Clock
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function Profile() {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.profile?.phone || '',
    company: user?.profile?.company || '',
    role: user?.profile?.role || '',
    location: user?.profile?.location || '',
    bio: user?.profile?.bio || '',
  });

  const stats = [
    { label: 'Portfolios Created', value: '24', icon: TrendingUp, color: '#7C3AED' },
    { label: 'Optimizations Run', value: '1,247', icon: Clock, color: '#7C3AED' },
    { label: 'Member Since', value: '2023', icon: Calendar, color: '#7C3AED' },
    { label: 'Verification', value: 'Verified', icon: Shield, color: '#7C3AED' },
  ];

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Full name is required');
      return;
    }

    setIsSaving(true);
    try {
      // We send everything except email, as email update is not supported here
      const { email, ...updateData } = formData;
      await updateProfile(updateData as any);
      setIsEditing(false);
    } catch (e) {
      // Context handles the toast
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsUploading(false);
    toast.success('Profile picture updated');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-white">Profile</h1>
        <p className="text-[#94A3B8]">Manage your personal information and preferences</p>
      </motion.div>

      {/* Profile Header Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-[#111827]/50 border-[#1E293B] overflow-hidden">
          {/* Cover Image */}
          <div className="h-32 bg-gradient-to-r from-[#7C3AED]/30 via-[#0048B4]/30 to-[#7C3AED]/30" />
          
          <CardContent className="p-6 -mt-12">
            <div className="flex flex-col md:flex-row items-start md:items-end gap-6">
              {/* Avatar */}
              <div className="relative">
                <div 
                  onClick={handleAvatarClick}
                  className="w-24 h-24 rounded-2xl bg-gradient-to-br from-[#7C3AED] to-[#0048B4] flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity border-4 border-[#7C3AED]"
                >
                  {isUploading ? (
                    <div className="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <span className="text-white text-3xl font-bold">{formData.name.charAt(0)}</span>
                  )}
                </div>
                <button 
                  onClick={handleAvatarClick}
                  className="absolute -bottom-2 -right-2 w-8 h-8 bg-[#111827] border border-[#1E293B] rounded-full flex items-center justify-center text-[#94A3B8] hover:text-white hover:border-[#FF6200] transition-colors"
                >
                  <Camera className="w-4 h-4" />
                </button>
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept="image/*" 
                  className="hidden" 
                  onChange={handleFileChange}
                />
              </div>

              {/* Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-2xl font-bold text-white">{formData.name}</h2>
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/30">
                    <Shield className="w-3 h-3 text-[#10B981]" />
                    <span className="text-[#10B981] text-xs">Verified</span>
                  </div>
                </div>
                <p className="text-[#94A3B8]">{formData.role} at {formData.company}</p>
                <div className="flex items-center gap-4 mt-2 text-sm text-[#64748B]">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {formData.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <Mail className="w-4 h-4" />
                    {formData.email}
                  </span>
                </div>
              </div>

              {/* Edit Button */}
              <Button
                onClick={() => isEditing ? handleSave() : setIsEditing(true)}
                disabled={isSaving}
                className={isEditing ? 'bg-[#7C3AED] hover:bg-[#8B5CF6]' : 'bg-gradient-to-r from-[#7C3AED] to-[#8B5CF6]'}
              >
                {isEditing ? (
                  isSaving ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Save
                    </>
                  )
                ) : (
                  <>
                    <Edit2 className="w-4 h-4 mr-2" />
                    Edit Profile
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <Card key={i} className="bg-[#111827]/50 border-[#1E293B]">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${stat.color}20` }}>
                    <Icon className="w-5 h-5" style={{ color: stat.color }} />
                  </div>
                </div>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-[#64748B] text-sm">{stat.label}</p>
              </CardContent>
            </Card>
          );
        })}
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Personal Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader>
              <CardTitle className="text-white">Personal Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-[#94A3B8] mb-2">Full Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#FF6200]/50"
                    />
                  ) : (
                    <div className="flex items-center gap-3 px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl">
                      <User className="w-5 h-5 text-[#64748B]" />
                      <span className="text-white">{formData.name}</span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#94A3B8] mb-2">Email Address</label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#FF6200]/50"
                    />
                  ) : (
                    <div className="flex items-center gap-3 px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl">
                      <Mail className="w-5 h-5 text-[#64748B]" />
                      <span className="text-white">{formData.email}</span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#94A3B8] mb-2">Phone Number</label>
                  {isEditing ? (
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#FF6200]/50"
                    />
                  ) : (
                    <div className="flex items-center gap-3 px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl">
                      <Phone className="w-5 h-5 text-[#64748B]" />
                      <span className="text-white">{formData.phone}</span>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#94A3B8] mb-2">Company</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#FF6200]/50"
                    />
                  ) : (
                    <div className="flex items-center gap-3 px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl">
                      <Building2 className="w-5 h-5 text-[#64748B]" />
                      <span className="text-white">{formData.company}</span>
                    </div>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-[#94A3B8] mb-2">Bio</label>
                  {isEditing ? (
                    <textarea
                      value={formData.bio}
                      onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl text-white focus:outline-none focus:border-[#FF6200]/50 resize-none"
                    />
                  ) : (
                    <div className="px-4 py-3 bg-[#0d1117] border border-[#1E293B] rounded-xl">
                      <p className="text-white leading-relaxed">{formData.bio}</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Sidebar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-6"
        >
          {/* Badges */}
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-[#F59E0B]" />
                Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: 'Early Adopter', desc: 'Joined in 2023', color: '#FF6200' },
                  { name: 'Power User', desc: '100+ optimizations', color: '#0048B4' },
                  { name: 'Sharpe Master', desc: 'Ratio > 1.0', color: '#10B981' },
                ].map((badge, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${badge.color}20` }}
                    >
                      <Award className="w-5 h-5" style={{ color: badge.color }} />
                    </div>
                    <div>
                      <p className="text-white font-medium text-sm">{badge.name}</p>
                      <p className="text-[#64748B] text-xs">{badge.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Account Status */}
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader>
              <CardTitle className="text-white">Account Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8]">Plan</span>
                  <span className="px-2 py-1 rounded-full bg-[#FF6200]/10 text-[#FF6200] text-xs font-medium">
                    Professional
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8]">Status</span>
                  <span className="flex items-center gap-1 text-[#10B981] text-sm">
                    <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8]">Renewal</span>
                  <span className="text-white text-sm">Dec 31, 2025</span>
                </div>
                <div className="pt-4 border-t border-[#1E293B]">
                  <Button variant="outline" className="w-full border-[#1E293B] text-[#94A3B8]">
                    Upgrade Plan
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
