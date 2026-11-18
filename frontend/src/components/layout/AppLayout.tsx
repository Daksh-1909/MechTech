import React, { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  Cpu,
  Layers,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Wrench,
  X,
  Radio,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { motion, useReducedMotion } from 'framer-motion'

export const AppLayout: React.FC = () => {
  const reduceMotion = useReducedMotion()
  const { user, organization, logout, isPlatformAdmin } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Equipment Fleet', path: '/equipment', icon: Layers },
    { label: 'Live Telemetry & Rules', path: '/monitoring', icon: Radio },
    { label: 'Anomaly Alerts', path: '/alerts', icon: AlertTriangle },
    { label: 'Hybrid Diagnostics', path: '/diagnostics', icon: Cpu },
    { label: 'Maintenance Orders', path: '/maintenance', icon: Wrench },
    ...(isPlatformAdmin ? [{ label: 'Admin & Auditing', path: '/admin', icon: ShieldCheck }] : []),
  ]

  const userRoleDisplay =
    user?.roles?.[0] || (isPlatformAdmin ? 'Platform Admin' : 'Viewer')

  return (
    <div className="mechtech-shell relative min-h-screen flex flex-col bg-canvas text-primary font-sans antialiased overflow-x-hidden">
      {/* Top Advisory Disclaimer Bar — Liquid Glass Banner */}
      <div className="relative z-20 border-b border-border bg-raised px-4 py-1.5 text-center text-xs text-secondary font-mono flex items-center justify-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
        <span className="font-semibold uppercase tracking-wider text-accent">Academic Advisory System:</span>
        <span className="hidden sm:inline">Telemetry & ML predictions are simulated. Physical human inspection required before maintenance action.</span>
        <span className="sm:hidden">Simulated data only. Physical verification required.</span>
      </div>

      <div className="relative z-10 flex-1 flex overflow-hidden">
        {/* Mobile Sidebar Backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xl lg:hidden transition-opacity duration-300"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar — Floating Frosted Liquid Glass Panel */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 w-64 lg:static lg:translate-x-0 transform transition-all duration-300 cubic-bezier(0.16,1,0.3,1) flex flex-col ${
            sidebarOpen ? 'translate-x-0 p-3' : '-translate-x-full lg:p-3'
          }`}
        >
          <div className="h-full flex flex-col rounded-2xl glass-panel border border-border overflow-hidden">
            {/* Logo Header */}
            <div className="h-16 px-5 flex items-center justify-between border-b border-border">
              <Link to="/" className="flex items-center gap-3 group">
                <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center text-black font-bold group-hover:scale-105 transition-transform duration-300">
                  <Activity className="w-5 h-5 text-black" />
                </div>
                <div>
                  <div className="font-bold text-base tracking-tight text-primary flex items-center gap-1.5">
                    MechTech
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/30">
                      v1.0
                    </span>
                  </div>
                  <span className="text-[10px] text-muted font-mono block -mt-0.5">
                    Detect. Diagnose. Maintain.
                  </span>
                </div>
              </Link>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden text-secondary hover:text-primary p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Org Selector / Info Pill */}
            <div className="p-3">
              <div className="p-3 rounded-xl bg-raised border border-border">
                <div className="text-[9px] font-mono uppercase tracking-widest text-muted flex items-center justify-between">
                  <span>Organization</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                </div>
                <div className="font-semibold text-xs text-primary truncate mt-1">
                  {organization?.name || 'Academic Demonstration'}
                </div>
              </div>
            </div>

            {/* Nav Items with Shared layoutId Active Surface */}
            <nav className="flex-1 px-3 space-y-1.5 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors duration-200 ${
                      isActive
                        ? 'text-accent'
                        : 'text-secondary hover:text-primary hover:bg-raised'
                    }`}
                  >
                    {isActive && (
                      <motion.span
                        layoutId="workspace-nav-indicator"
                        className="nav-active-surface"
                        transition={
                          reduceMotion
                            ? { duration: 0 }
                            : { type: 'spring', stiffness: 400, damping: 30, mass: 0.6 }
                        }
                      />
                    )}
                    <Icon className={`relative z-10 w-4 h-4 ${isActive ? 'text-accent' : 'text-muted'}`} />
                    <span className="relative z-10 truncate">{item.label}</span>
                  </Link>
                )
              })}
            </nav>

            {/* User Profile Glass Footer */}
            <div className="p-3 border-t border-border bg-raised">
              <div className="flex items-center justify-between p-2 rounded-xl bg-surface border border-border">
                <div className="truncate pr-2">
                  <div className="text-xs font-semibold text-primary truncate">
                    {user?.display_name || 'Technician'}
                  </div>
                  <div className="text-[10px] text-muted truncate flex items-center gap-1.5 mt-0.5 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                    <span className="capitalize">{userRoleDisplay.replace('_', ' ')}</span>
                  </div>
                </div>
                <button
                  onClick={() => logout()}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-secondary hover:text-accent hover:bg-accent/10 border border-transparent hover:border-accent/30 transition-all"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Top Glass Navbar */}
          <header className="h-16 px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur-2xl bg-canvas/80 border-b border-border shadow-sm">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-xl text-secondary hover:text-primary glass-btn"
              >
                <Menu className="w-4 h-4" />
              </button>
              <h1 className="text-sm font-semibold text-primary hidden sm:flex items-center gap-2">
                <span>
                  {navItems.find((n) =>
                    n.path === '/'
                      ? location.pathname === '/'
                      : location.pathname.startsWith(n.path)
                  )?.label || 'Condition Monitoring'}
                </span>
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="glass-pill glass-pill-ok">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                <span>API Gateway: 127.0.0.1:8000</span>
              </div>
            </div>
          </header>

          {/* Page Content Viewport */}
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto animate-in fade-in duration-300">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
