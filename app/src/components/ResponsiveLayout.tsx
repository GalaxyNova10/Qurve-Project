import React, { useState, useEffect } from 'react';
import { Menu, X, User, Settings, BarChart3, Shield, Database } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  className?: string;
}

export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ 
  children, 
  sidebar, 
  header, 
  className 
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
      setIsTablet(window.innerWidth >= 768 && window.innerWidth < 1024);
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  return (
    <div className={cn('min-h-screen bg-gray-50', className)}>
      {/* Mobile Header */}
      {(isMobile || isTablet) && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Toggle sidebar"
              >
                {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <h1 className="text-lg font-semibold text-gray-900">QURVE AI</h1>
            </div>
            
            {header && (
              <div className="flex items-center space-x-4">
                {header}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Desktop Header */}
      {!isMobile && !isTablet && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900">QURVE AI</h1>
              <nav className="hidden md:flex space-x-6">
                <a href="/dashboard" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </a>
                <a href="/benchmarks" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Benchmarks
                </a>
                <a href="/replay" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Replay
                </a>
                <a href="/admin" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Admin
                </a>
              </nav>
            </div>
            
            {header && (
              <div className="flex items-center space-x-4">
                {header}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sidebar Overlay for Mobile */}
      {isMobile && isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        'fixed top-0 left-0 z-50 w-64 h-full bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out',
        isMobile ? (isSidebarOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0',
        isTablet ? (isSidebarOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'
      )}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
          {(isMobile || isTablet) && (
            <button
              onClick={closeSidebar}
              className="p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {sidebar || (
            <nav className="space-y-2">
              <div className="space-y-1">
                <a
                  href="/dashboard"
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                >
                  <BarChart3 className="w-5 h-5" />
                  <span>Dashboard</span>
                </a>
                <a
                  href="/benchmarks"
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                >
                  <Database className="w-5 h-5" />
                  <span>Benchmarks</span>
                </a>
                <a
                  href="/replay"
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                >
                  <Shield className="w-5 h-5" />
                  <span>Replay</span>
                </a>
                <a
                  href="/admin"
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                >
                  <Settings className="w-5 h-5" />
                  <span>Admin</span>
                </a>
              </div>
            </nav>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <User className="w-5 h-5 text-gray-500" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">User Profile</p>
              <p className="text-xs text-gray-500 truncate">user@qurve.ai</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={cn(
        'flex-1 transition-all duration-300 ease-in-out',
        isMobile ? 'ml-0' : 'ml-64',
        isTablet ? (isSidebarOpen ? 'ml-64' : 'ml-0') : 'ml-64'
      )}>
        {/* Top padding for mobile header */}
        {(isMobile || isTablet) && (
          <div className="h-16" />
        )}

        {/* Desktop top padding */}
        {!isMobile && !isTablet && (
          <div className="h-16" />
        )}

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

// Responsive Grid Component
interface ResponsiveGridProps {
  children: React.ReactNode;
  cols?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
    large?: number;
  };
  gap?: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
    large?: string;
  };
  className?: string;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({ 
  children, 
  cols = { mobile: 1, tablet: 2, desktop: 3, large: 4 },
  gap = { mobile: 'gap-4', tablet: 'gap-6', desktop: 'gap-6', large: 'gap-8' },
  className 
}) => {
  const [currentCols, setCurrentCols] = useState(cols.desktop);
  const [currentGap, setCurrentGap] = useState(gap.desktop);

  useEffect(() => {
    const updateGrid = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setCurrentCols(cols.mobile || 1);
        setCurrentGap(gap.mobile || 'gap-4');
      } else if (width < 1024) {
        setCurrentCols(cols.tablet || 2);
        setCurrentGap(gap.tablet || 'gap-6');
      } else if (width < 1280) {
        setCurrentCols(cols.desktop || 3);
        setCurrentGap(gap.desktop || 'gap-6');
      } else {
        setCurrentCols(cols.large || 4);
        setCurrentGap(gap.large || 'gap-8');
      }
    };

    updateGrid();
    window.addEventListener('resize', updateGrid);
    return () => window.removeEventListener('resize', updateGrid);
  }, [cols, gap]);

  return (
    <div 
      className={cn(
        `grid grid-cols-${currentCols}`,
        currentGap,
        className
      )}
      style={{
        gridTemplateColumns: `repeat(${currentCols}, minmax(0, 1fr))`
      }}
    >
      {children}
    </div>
  );
};

// Responsive Card Component
interface ResponsiveCardProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  footer?: React.ReactNode;
  className?: string;
  padding?: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
  };
}

export const ResponsiveCard: React.FC<ResponsiveCardProps> = ({ 
  children, 
  title, 
  description, 
  footer, 
  className,
  padding = { mobile: 'p-4', tablet: 'p-6', desktop: 'p-6' }
}) => {
  const [currentPadding, setCurrentPadding] = useState(padding.desktop);

  useEffect(() => {
    const updatePadding = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setCurrentPadding(padding.mobile || 'p-4');
      } else if (width < 1024) {
        setCurrentPadding(padding.tablet || 'p-6');
      } else {
        setCurrentPadding(padding.desktop || 'p-6');
      }
    };

    updatePadding();
    window.addEventListener('resize', updatePadding);
    return () => window.removeEventListener('resize', updatePadding);
  }, [padding]);

  return (
    <div className={cn(
      'bg-white rounded-lg shadow-sm border border-gray-200',
      currentPadding,
      className
    )}>
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
          )}
          {description && (
            <p className="text-sm text-gray-600">{description}</p>
          )}
        </div>
      )}
      
      <div className="flex-1">
        {children}
      </div>
      
      {footer && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {footer}
        </div>
      )}
    </div>
  );
};

// Responsive Table Component
interface ResponsiveTableProps {
  children: React.ReactNode;
  className?: string;
  breakpoint?: 'sm' | 'md' | 'lg' | 'xl';
}

export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({ 
  children, 
  className,
  breakpoint = 'md'
}) => {
  const [isResponsive, setIsResponsive] = useState(false);

  useEffect(() => {
    const checkResponsive = () => {
      const width = window.innerWidth;
      const breakpoints = { sm: 640, md: 768, lg: 1024, xl: 1280 };
      setIsResponsive(width < breakpoints[breakpoint]);
    };

    checkResponsive();
    window.addEventListener('resize', checkResponsive);
    return () => window.removeEventListener('resize', checkResponsive);
  }, [breakpoint]);

  return (
    <div className={cn(
      'overflow-x-auto',
      isResponsive && 'block lg:hidden',
      className
    )}>
      <table className={cn(
        'min-w-full divide-y divide-gray-200',
        !isResponsive && 'hidden lg:table',
        className
      )}>
        {children}
      </table>
      
      {/* Mobile Card View */}
      {isResponsive && (
        <div className="lg:hidden space-y-4">
          {children}
        </div>
      )}
    </div>
  );
};

// Responsive Text Component
interface ResponsiveTextProps {
  children: React.ReactNode;
  size?: {
    mobile?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
    tablet?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
    desktop?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  };
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold';
  className?: string;
}

export const ResponsiveText: React.FC<ResponsiveTextProps> = ({ 
  children, 
  size = { mobile: 'sm', tablet: 'sm', desktop: 'base' },
  weight = 'normal',
  className 
}) => {
  const [currentSize, setCurrentSize] = useState(size.desktop);

  useEffect(() => {
    const updateSize = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setCurrentSize(size.mobile || 'sm');
      } else if (width < 1024) {
        setCurrentSize(size.tablet || 'sm');
      } else {
        setCurrentSize(size.desktop || 'base');
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [size]);

  const sizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  const weightClasses = {
    light: 'font-light',
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold'
  };

  return (
    <span className={cn(
      sizeClasses[currentSize as keyof typeof sizeClasses],
      weightClasses[weight],
      className
    )}>
      {children}
    </span>
  );
};
