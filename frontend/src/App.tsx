import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './context/AuthContext'
import AppLayout from './components/layout/AppLayout'

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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-xs font-mono text-cyan-400 gap-3">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        <span>Loading MechTech Condition Monitoring...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Fallback Spinner
const PageFallback = () => (
  <div className="p-12 flex flex-col items-center justify-center text-xs font-mono text-slate-400 gap-3">
    <div className="w-6 h-6 border-2 border-slate-600 border-t-cyan-400 rounded-full animate-spin" />
    <span>Loading View...</span>
  </div>
)

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageFallback />}>
            <Routes>
              {/* Public Auth Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Workspace Layout */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="equipment" element={<EquipmentListPage />} />
                <Route path="equipment/:id" element={<EquipmentDetailPage />} />
                <Route path="monitoring" element={<MonitoringPage />} />
                <Route path="alerts" element={<AlertsPage />} />
                <Route path="diagnostics" element={<DiagnosticsPage />} />
                <Route path="maintenance" element={<MaintenancePage />} />
                <Route path="admin" element={<AdminPage />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
