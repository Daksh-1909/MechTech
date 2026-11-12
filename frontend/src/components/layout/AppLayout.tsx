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
  FileText,
  UserCheck,
  Radio,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export const AppLayout: React.FC = () => {
  const { user, organization, logout, isPlatformAdmin, isMaintainer } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Equipment Fleet', path: '/equipment', icon: Layers },
    { label: 'Live Telemetry & Rules', path: '/monitoring', icon: Radio },
    { label: 'Anomaly Alerts', path: '/alerts', icon: AlertTriangle },
    { label: 'Hybrid Diagnostics', path: '/diagnostics', icon: Cpu },
    { label: 'Maintenance Orders', path: '/maintenance', icon: Wrench },
    ...(isPlatformAdmin
      ? [{ label: 'Admin & Auditing', path: '/admin', icon: ShieldCheck }]
      : []),
  ]

  const userRoleDisplay =
    user?.roles?.[0] || (user?.is_superuser ? 'Platform Admin' : 'Viewer')

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Advisory Disclaimer Bar */}
      <div className="bg-gradient-to-r from-amber-950/80 via-amber-900/60 to-amber-950/80 border-b border-amber-800/40 px-4 py-1.5 text-center text-xs text-amber-200/90 font-mono flex items-center justify-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
        <span className="font-semibold uppercase tracking-wider">Academic Advisory System:</span>
        <span className="hidden sm:inline">Telemetry & ML predictions are simulated. Physical human inspection required before maintenance action.</span>
        <span className="sm:hidden">Simulated data only. Verification required.</span>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Mobile Sidebar Backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800/80 flex flex-col transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {/* Logo Header */}
          <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-cyan-500/20">
                <Activity className="w-5 h-5 text-slate-950" />
              </div>
              <div>
                <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                  MechTech
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
                    v1.0
                  </span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono block -mt-0.5">
                  Detect. Diagnose. Maintain.
                </span>
              </div>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-slate-400 hover:text-white p-1 rounded-md"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Org Selector / Info */}
          <div className="px-4 py-3 mx-3 my-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Organization</div>
            <div className="font-semibold text-slate-200 truncate mt-0.5">
              {organization?.name || 'Academic Demonstration'}
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
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
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          {/* User profile footer */}
          <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div className="truncate pr-2">
                <div className="text-sm font-semibold text-slate-200 truncate">{user?.name}</div>
                <div className="text-xs text-slate-400 truncate flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="capitalize">{userRoleDisplay.replace('_', ' ')}</span>
                </div>
              </div>
              <button
                onClick={() => logout()}
                title="Sign out"
                className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-slate-950">
          {/* Top Navbar */}
          <header className="h-16 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/40 backdrop-blur-md sticky top-0 z-30">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <Menu className="w-5 h-5" />
              </button>
              <h1 className="text-base font-semibold text-slate-200 hidden sm:block">
                {navItems.find((n) =>
                  n.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(n.path)
                )?.label || 'Monitoring Platform'}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-xs font-mono text-emerald-300">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                API Connected: 127.0.0.1:8000
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout

