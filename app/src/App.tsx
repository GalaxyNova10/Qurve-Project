import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Toaster } from 'sonner';

// Layouts
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/layout/AuthLayout';

// Lazy loaded pages
const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Performance = lazy(() => import('./pages/Performance'));
const Allocation = lazy(() => import('./pages/Allocation'));
const Benchmarking = lazy(() => import('./pages/Benchmarking'));
const GPUTelemetry = lazy(() => import('./pages/GPUTelemetry'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Monitoring = lazy(() => import('./pages/Monitoring'));
const Settings = lazy(() => import('./pages/Settings'));
const Profile = lazy(() => import('./pages/Profile'));
const Terms = lazy(() => import('./pages/Terms'));
const Privacy = lazy(() => import('./pages/Privacy'));
const Security = lazy(() => import('./pages/Security'));

// Protected Route
import ProtectedRoute from './components/layout/ProtectedRoute';

// Simple loading fallback component
const LoadingFallback = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-900">
    <div className="text-white text-lg">Loading...</div>
  </div>
);

// TanStack Query client with sensible defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,      // 30s
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Landing />} />
              
              {/* Auth Routes */}
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>

              {/* Protected Routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<MainLayout />}>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/performance" element={<Performance />} />
                  <Route path="/allocation" element={<Allocation />} />
                  <Route path="/benchmarking" element={<Benchmarking />} />
                  <Route path="/gpu-telemetry" element={<GPUTelemetry />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/profile" element={<Profile />} />
                </Route>
              </Route>

              {/* Legal Pages */}
              <Route path="/terms" element={<Terms />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/security" element={<Security />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </Router>
        <Toaster 
          position="top-right" 
          toastOptions={{
            style: {
              background: '#111827',
              border: '1px solid #1E293B',
              color: '#FFFFFF',
            },
          }}
        />
      </AuthProvider>
    </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
