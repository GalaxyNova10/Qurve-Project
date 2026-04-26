import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  TrendingUp,
  PieChart,
  Cpu,
  BarChart3,
  Settings,
  User,
  LogOut,
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useState } from 'react';
import { toast } from 'sonner';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/performance', label: 'Performance', icon: TrendingUp },
  { path: '/allocation', label: 'Allocation', icon: PieChart },
  { path: '/gpu-telemetry', label: 'GPU Telemetry', icon: Cpu },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const bottomItems = [
  { path: '/profile', label: 'Profile', icon: User },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { logout, user } = useAuth();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  return (
    <motion.aside
      initial={{ x: -100 }}
      animate={{ x: 0 }}
      className={`fixed left-0 top-0 h-full bg-[#0d1117]/95 backdrop-blur-xl border-r border-[#1E293B]/50 z-50 transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="p-6 border-b border-[#1E293B]/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6200] to-[#0048B4] flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h1 className="font-bold text-white text-lg">QUBO</h1>
              <p className="text-xs text-[#94A3B8]">Portfolio AI</p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                ${isActive 
                  ? 'bg-gradient-to-r from-[#FF6200]/20 to-[#0048B4]/20 text-white border border-[#FF6200]/30' 
                  : 'text-[#94A3B8] hover:bg-[#1E293B]/50 hover:text-white'
                }
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-[#FF6200]' : 'group-hover:text-[#FF6200]'}`} />
              {!collapsed && (
                <span className="font-medium text-sm">{item.label}</span>
              )}
              {isActive && !collapsed && (
                <motion.div
                  layoutId="activeIndicator"
                  className="ml-auto w-1.5 h-1.5 rounded-full bg-[#FF6200]"
                />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-4 my-4 border-t border-[#1E293B]/50" />

      {/* Bottom Items */}
      <nav className="px-4 space-y-1">
        {bottomItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                ${isActive 
                  ? 'bg-gradient-to-r from-[#FF6200]/20 to-[#0048B4]/20 text-white border border-[#FF6200]/30' 
                  : 'text-[#94A3B8] hover:bg-[#1E293B]/50 hover:text-white'
                }
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-[#FF6200]' : 'group-hover:text-[#FF6200]'}`} />
              {!collapsed && <span className="font-medium text-sm">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* User & Logout */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#1E293B]/50">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#0048B4] to-[#FF6200] flex items-center justify-center flex-shrink-0">
            <span className="text-white font-semibold text-sm">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-white font-medium text-sm truncate">{user?.name}</p>
              <p className="text-[#64748B] text-xs truncate">{user?.email}</p>
            </div>
          )}
        </div>
        
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-2.5 w-full rounded-xl text-[#94A3B8] hover:bg-[#EF4444]/10 hover:text-[#EF4444] transition-all duration-200"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="font-medium text-sm">Logout</span>}
        </button>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-24 w-6 h-6 bg-[#1E293B] border border-[#2D3748] rounded-full flex items-center justify-center text-[#94A3B8] hover:text-white hover:border-[#FF6200] transition-all"
      >
        {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
      </button>
    </motion.aside>
  );
}
