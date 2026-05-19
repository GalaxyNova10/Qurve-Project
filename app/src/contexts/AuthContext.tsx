import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { toast } from 'sonner';

export interface UserProfile {
  phone?: string;
  company?: string;
  role?: string;
  location?: string;
  bio?: string;
  avatar?: string;
}

export interface UserSettings {
  language?: string;
  timezone?: string;
  currency?: string;
  dateFormat?: string;
  emailAlerts?: boolean;
  pushNotifications?: boolean;
  portfolioUpdates?: boolean;
  optimizationComplete?: boolean;
  marketOpen?: boolean;
  weeklyReport?: boolean;
  twoFactor?: boolean;
  biometric?: boolean;
  sessionTimeout?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user';
  createdAt: Date;
  profile?: UserProfile;
  settings?: UserSettings;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User> & Partial<UserProfile>) => Promise<void>;
  updateSettings: (data: Partial<UserSettings>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth
    const storedUser = localStorage.getItem('qubo_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, _password: string) => {
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', _password);

      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      const token = data.access_token;
      
      // Store token
      localStorage.setItem('qubo_token', token);

      // Fetch user profile
      const userResponse = await fetch('/api/v1/auth/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!userResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }
      
      const userData = await userResponse.json();
      
      const loggedUser: User = {
        id: userData.username,
        email: userData.email || userData.username,
        name: userData.full_name || userData.username.split('@')[0],
        role: 'admin',
        createdAt: new Date(),
        profile: userData.profile || {},
        settings: {
          language: userData.settings?.language || 'en',
          timezone: userData.settings?.timezone || 'Asia/Kolkata',
          currency: userData.settings?.currency || 'INR',
          dateFormat: userData.settings?.date_format || 'DD/MM/YYYY',
          emailAlerts: userData.settings?.email_alerts ?? true,
          pushNotifications: userData.settings?.push_notifications ?? true,
          portfolioUpdates: userData.settings?.portfolio_updates ?? true,
          optimizationComplete: userData.settings?.optimization_complete ?? true,
          marketOpen: userData.settings?.market_open ?? false,
          weeklyReport: userData.settings?.weekly_report ?? true,
          twoFactor: userData.settings?.two_factor ?? false,
          biometric: userData.settings?.biometric ?? false,
          sessionTimeout: userData.settings?.session_timeout || '30',
        }
      };
      
      setUser(loggedUser);
      localStorage.setItem('qubo_user', JSON.stringify(loggedUser));
      toast.success('Welcome back!');
    } catch (error) {
      toast.error('Invalid credentials');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (name: string, email: string, _password: string) => {
    void _password; // Intentionally unused in mock
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockUser: User = {
        id: Date.now().toString(),
        email,
        name,
        role: 'user',
        createdAt: new Date(),
      };
      
      setUser(mockUser);
      localStorage.setItem('qubo_user', JSON.stringify(mockUser));
      toast.success('Account created successfully!');
    } catch (error) {
      toast.error('Registration failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('qubo_user');
    localStorage.removeItem('qubo_token');
    toast.success('Logged out successfully');
  };

  const updateProfile = async (data: Partial<User> & Partial<UserProfile>) => {
    if (!user) return;
    try {
        const token = localStorage.getItem('qubo_token');
        if (!token) throw new Error("No token");

        const response = await fetch('/api/v1/auth/users/me/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update profile');
        const updatedUserData = await response.json();
        
        const updatedUser = { ...user, name: updatedUserData.full_name, profile: updatedUserData.profile };
        setUser(updatedUser);
        localStorage.setItem('qubo_user', JSON.stringify(updatedUser));
        toast.success('Profile updated');
    } catch (e) {
        toast.error('Failed to update profile');
        throw e;
    }
  };

  const updateSettings = async (data: Partial<UserSettings>) => {
    if (!user) return;
    try {
        const token = localStorage.getItem('qubo_token');
        if (!token) throw new Error("No token");

        const backendData = {
          language: data.language,
          timezone: data.timezone,
          currency: data.currency,
          date_format: data.dateFormat,
          email_alerts: data.emailAlerts,
          push_notifications: data.pushNotifications,
          portfolio_updates: data.portfolioUpdates,
          optimization_complete: data.optimizationComplete,
          market_open: data.marketOpen,
          weekly_report: data.weeklyReport,
          two_factor: data.twoFactor,
          biometric: data.biometric,
          session_timeout: data.sessionTimeout,
        };

        const response = await fetch('/api/v1/auth/users/me/settings', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(backendData)
        });
        if (!response.ok) throw new Error('Failed to update settings');
        
        const updatedUser = { ...user, settings: { ...user.settings, ...data } };
        setUser(updatedUser);
        localStorage.setItem('qubo_user', JSON.stringify(updatedUser));
        toast.success('Settings saved successfully');
    } catch (e) {
        toast.error('Failed to update settings');
        throw e;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
      updateProfile,
      updateSettings,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
