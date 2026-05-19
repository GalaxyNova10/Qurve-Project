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
  Activity,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useState } from 'react';
import { toast } from 'sonner';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/performance', label: 'Performance', icon: TrendingUp },
  { path: '/allocation', label: 'Allocation', icon: PieChart },
  { path: '/benchmarking', label: 'Benchmarking', icon: Activity },
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
      className={`fixed left-0 top-0 h-full bg-card/95 backdrop-blur-xl border-r border-border/50 z-50 transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="p-6 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary glow-purple flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h1 className="font-bold text-foreground text-lg tracking-wide">Qurve</h1>
              <p className="text-xs text-muted-foreground">Portfolio AI</p>
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
                  ? 'bg-primary/20 text-foreground border border-primary/30 glow-purple' 
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                }
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-primary' : 'group-hover:text-primary'}`} />
              {!collapsed && (
                <span className="font-medium text-sm">{item.label}</span>
              )}
              {isActive && !collapsed && (
                <motion.div
                  layoutId="activeIndicator"
                  className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
                />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-4 my-4 border-t border-border/50" />

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
                  ? 'bg-primary/20 text-foreground border border-primary/30 glow-purple' 
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                }
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-primary' : 'group-hover:text-primary'}`} />
              {!collapsed && <span className="font-medium text-sm">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* User & Logout */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border/50">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-primary glow-purple flex items-center justify-center flex-shrink-0">
            <span className="text-white font-semibold text-sm">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-foreground font-medium text-sm truncate">{user?.name}</p>
              <p className="text-muted-foreground text-xs truncate">{user?.email}</p>
            </div>
          )}
        </div>
        
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-2.5 w-full rounded-xl text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="font-medium text-sm">Logout</span>}
        </button>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-24 w-6 h-6 bg-card border border-border rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-primary hover:glow-purple transition-all"
      >
        {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
      </button>
    </motion.aside>
  );
}
