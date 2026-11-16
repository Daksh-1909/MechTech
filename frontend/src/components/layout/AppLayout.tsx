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

export const AppLayout: React.FC = () => {
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

  const userRoleDisplay = user?.roles?.[0] || 'Viewer'

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 font-sans text-slate-100 antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Advisory Disclaimer Bar */}
      <div className="flex items-center justify-center gap-2 border-b border-amber-800/40 bg-gradient-to-r from-amber-950/80 via-amber-900/60 to-amber-950/80 px-4 py-1.5 text-center font-mono text-xs text-amber-200/90">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
        <span className="font-semibold tracking-wider uppercase">Academic Advisory System:</span>
        <span className="hidden sm:inline">
          Telemetry & ML predictions are simulated. Physical human inspection required before
          maintenance action.
        </span>
        <span className="sm:hidden">Simulated data only. Verification required.</span>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Mobile Sidebar Backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-64 transform flex-col border-r border-slate-800/80 bg-slate-900 transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {/* Logo Header */}
          <div className="flex h-16 items-center justify-between border-b border-slate-800 px-6">
            <Link to="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 font-bold text-slate-950 shadow-lg shadow-cyan-500/20">
                <Activity className="h-5 w-5 text-slate-950" />
              </div>
              <div>
                <span className="flex items-center gap-1.5 text-base font-bold tracking-tight text-white">
                  MechTech
                  <span className="rounded border border-cyan-800/50 bg-cyan-950 px-1.5 py-0.5 font-mono text-[10px] text-cyan-400">
                    v1.0
                  </span>
                </span>
                <span className="-mt-0.5 block font-mono text-[10px] text-slate-400">
                  Detect. Diagnose. Maintain.
                </span>
              </div>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="rounded-md p-1 text-slate-400 hover:text-white lg:hidden"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Org Selector / Info */}
          <div className="mx-3 my-3 rounded-lg border border-slate-800/80 bg-slate-950/60 px-4 py-3 text-xs">
            <div className="font-mono text-[10px] tracking-wider text-slate-400 uppercase">
              Organization
            </div>
            <div className="mt-0.5 truncate font-semibold text-slate-200">
              {organization?.name || 'Academic Demonstration'}
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive =
                item.path === '/dashboard'
                  ? location.pathname === '/dashboard'
                  : location.pathname.startsWith(item.path)
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border border-cyan-500/30 bg-cyan-500/10 text-cyan-400'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          {/* User profile footer */}
          <div className="border-t border-slate-800/80 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="truncate pr-2">
                <div className="truncate text-sm font-semibold text-slate-200">
                  {user?.display_name}
                </div>
                <div className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="capitalize">{userRoleDisplay.replace('_', ' ')}</span>
                </div>
              </div>
              <button
                onClick={() => logout()}
                title="Sign out"
                className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-rose-950/30 hover:text-rose-400"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex min-w-0 flex-1 flex-col overflow-y-auto bg-slate-950">
          {/* Top Navbar */}
          <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800/80 bg-slate-900/40 px-6 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
              >
                <Menu className="h-5 w-5" />
              </button>
              <h1 className="hidden text-base font-semibold text-slate-200 sm:block">
                {navItems.find((n) =>
                  n.path === '/dashboard'
                    ? location.pathname === '/dashboard'
                    : location.pathname.startsWith(n.path),
                )?.label || 'Monitoring Platform'}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-full border border-emerald-800/40 bg-emerald-950/40 px-3 py-1 font-mono text-xs text-emerald-300 md:flex">
                <span className="h-2 w-2 animate-ping rounded-full bg-emerald-400" />
                API Connected: 127.0.0.1:8000
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="mx-auto w-full max-w-7xl flex-1 p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
