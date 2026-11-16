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
  Sparkles,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export const AppLayout: React.FC = () => {
  const { user, organization, logout, isPlatformAdmin } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Equipment Fleet', path: '/equipment', icon: Layers },
    { label: 'Live Telemetry & Rules', path: '/monitoring', icon: Radio },
    { label: 'Anomaly Alerts', path: '/alerts', icon: AlertTriangle },
    { label: 'Hybrid Diagnostics', path: '/diagnostics', icon: Cpu },
    { label: 'Maintenance Orders', path: '/maintenance', icon: Wrench },
    ...(isPlatformAdmin ? [{ label: 'Admin & Auditing', path: '/admin', icon: ShieldCheck }] : []),
  ]

  const userRoleDisplay =
    user?.roles?.[0] || (user?.is_superuser ? 'Platform Admin' : 'Viewer')

  return (
    <div className="relative min-h-screen flex flex-col bg-[#050914] text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950 overflow-x-hidden">
      {/* Apple Liquid Ambient Aurora Glow Orbs */}
      <div className="liquid-glow-orb-cyan" />
      <div className="liquid-glow-orb-indigo" />
      <div className="liquid-glow-orb-emerald" />

      {/* Top Advisory Disclaimer Bar — Liquid Glass Banner */}
      <div className="relative z-20 backdrop-blur-2xl bg-amber-500/[0.08] border-b border-amber-400/20 px-4 py-1.5 text-center text-xs text-amber-200/90 font-mono flex items-center justify-center gap-2 shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
        <span className="font-semibold uppercase tracking-wider text-amber-300">Academic Advisory System:</span>
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
          <div className="h-full flex flex-col rounded-2xl glass-panel border border-white/[0.12] overflow-hidden">
            {/* Logo Header */}
            <div className="h-16 px-5 flex items-center justify-between border-b border-white/[0.08]">
              <Link to="/" className="flex items-center gap-3 group">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 via-sky-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold shadow-[0_0_20px_rgba(56,189,248,0.45),inset_0_1px_1px_rgba(255,255,255,0.6)] group-hover:scale-105 transition-transform duration-300">
                  <Activity className="w-5 h-5 text-slate-950" />
                </div>
                <div>
                  <div className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                    MechTech
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-400/15 text-cyan-300 border border-cyan-400/30">
                      v1.0
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono block -mt-0.5">
                    Detect. Diagnose. Maintain.
                  </span>
                </div>
              </Link>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Org Selector / Info Pill */}
            <div className="p-3">
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)]">
                <div className="text-[9px] font-mono uppercase tracking-widest text-slate-400 flex items-center justify-between">
                  <span>Organization</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
                </div>
                <div className="font-semibold text-xs text-slate-200 truncate mt-1">
                  {organization?.name || 'Academic Demonstration'}
                </div>
              </div>
            </div>

            {/* Nav Items */}
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
                    className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-500/25 to-blue-500/15 text-cyan-300 border border-cyan-400/40 shadow-[0_4px_16px_rgba(6,182,212,0.25),inset_0_1px_1px_rgba(255,255,255,0.25)] translate-x-1'
                        : 'text-slate-300 hover:bg-white/[0.06] hover:text-white hover:translate-x-0.5'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-300' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </Link>
                )
              })}
            </nav>

            {/* User Profile Glass Footer */}
            <div className="p-3 border-t border-white/[0.08] bg-white/[0.02]">
              <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                <div className="truncate pr-2">
                  <div className="text-xs font-semibold text-slate-200 truncate">{user?.name}</div>
                  <div className="text-[10px] text-slate-400 truncate flex items-center gap-1.5 mt-0.5 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span className="capitalize">{userRoleDisplay.replace('_', ' ')}</span>
                  </div>
                </div>
                <button
                  onClick={() => logout()}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-all"
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
          <header className="h-16 px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur-2xl bg-[#070d18]/50 border-b border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.3)]">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white glass-btn"
              >
                <Menu className="w-4 h-4" />
              </button>
              <h1 className="text-sm font-semibold text-slate-100 hidden sm:flex items-center gap-2">
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
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_rgba(52,211,153,0.9)]" />
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
