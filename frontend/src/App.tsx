import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './providers/ThemeProvider'
import AppLayout from './components/layout/AppLayout'
import LandingPage from './pages/LandingPage'

// Lazy-loaded pages to maintain high performance and avoid blocking initial paint
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const EquipmentListPage = lazy(() => import('./pages/EquipmentListPage'))
const EquipmentDetailPage = lazy(() => import('./pages/EquipmentDetailPage'))
const MonitoringPage = lazy(() => import('./pages/MonitoringPage'))
const AlertsPage = lazy(() => import('./pages/AlertsPage'))
const DiagnosticsPage = lazy(() => import('./pages/DiagnosticsPage'))
const MaintenancePage = lazy(() => import('./pages/MaintenancePage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const DesignPlaygroundPage = lazy(() => import('./pages/DesignPlaygroundPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-950 font-mono text-xs text-cyan-400">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
        <span>Loading MechTech Condition Monitoring...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <>{children}</>
}

// Fallback Spinner
const PageFallback = () => (
  <div className="flex flex-col items-center justify-center gap-3 p-12 font-mono text-xs text-slate-400">
    <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-cyan-400" />
    <span>Loading View...</span>
  </div>
)

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<PageFallback />}>
              <Routes>
                {/* Public pages */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/design-system" element={<DesignPlaygroundPage />} />

                {/* The website is public; the operational workspace requires a session. */}
                <Route
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/equipment" element={<EquipmentListPage />} />
                  <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
                  <Route path="/monitoring" element={<MonitoringPage />} />
                  <Route path="/alerts" element={<AlertsPage />} />
                  <Route path="/diagnostics" element={<DiagnosticsPage />} />
                  <Route path="/maintenance" element={<MaintenancePage />} />
                  <Route path="/admin" element={<AdminPage />} />
                </Route>

                {/* Catch-all redirect */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
