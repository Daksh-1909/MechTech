import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Activity, AlertCircle, ArrowRight, Lock, Mail, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export const LoginPage: React.FC = () => {
  const { login, error } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const requestedLocation = (
    location.state as { from?: { pathname?: string; search?: string; hash?: string } } | null
  )?.from
  const destination = requestedLocation?.pathname
    ? `${requestedLocation.pathname}${requestedLocation.search || ''}${requestedLocation.hash || ''}`
    : '/dashboard'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorMessage(null)
    try {
      await login(email, password)
      navigate(destination, { replace: true })
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickLogin = async (demoEmail: string) => {
    setEmail(demoEmail)
    setPassword('demo-password-123')
    setLoading(true)
    setErrorMessage(null)
    try {
      await login(demoEmail, 'demo-password-123')
      navigate(destination, { replace: true })
    } catch (err: any) {
      setErrorMessage(err.message || 'Demo login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page relative flex min-h-screen w-full flex-col items-center justify-center overflow-x-hidden bg-slate-950 p-4 font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Floating Apple Liquid Mesh Aurora Orbs */}
      <div className="liquid-glow-orb-cyan pointer-events-none" />
      <div className="liquid-glow-orb-indigo pointer-events-none" />
      <div className="liquid-glow-orb-emerald pointer-events-none" />

      <div className="relative z-10 w-full max-w-md min-w-0 space-y-6">
        {/* Brand Header */}
        <div className="space-y-3 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 font-bold text-slate-950 shadow-2xl shadow-cyan-500/30 transition-transform duration-500 hover:scale-105">
            <Activity className="h-8 w-8 text-slate-950" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white drop-shadow-md">
              Sign in to MechTech
            </h1>
            <p className="mt-1 font-mono text-xs text-slate-400">
              Equipment Condition Monitoring & Diagnostics Platform
            </p>
          </div>
        </div>

        {/* Apple Liquid Glass Login Card */}
        <div className="glass-panel w-full min-w-0 space-y-5 p-6 shadow-2xl sm:p-8">
          {(errorMessage || error) && (
            <div className="glass-panel flex items-center gap-2.5 border-rose-500/40 bg-rose-950/40 p-3.5 font-mono text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span className="min-w-0 break-words">{errorMessage || error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="mb-1.5 block font-mono text-slate-300">Email Address</label>
              <div className="relative">
                <Mail className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="glass-input login-input w-full"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block font-mono text-slate-300">Password</label>
              <div className="relative">
                <Lock className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="glass-input login-input w-full"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="glass-btn-primary flex w-full items-center justify-center gap-2 py-3 text-xs font-semibold text-white disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="border-t border-white/10 pt-4">
            <span className="mb-2.5 flex items-center justify-center gap-1.5 text-center font-mono text-[10px] tracking-wider text-slate-400 uppercase">
              <Sparkles className="h-3 w-3 text-amber-400" />
              Quick One-Click Demo Logins:
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.admin@example.com')}
                className="glass-panel-interactive rounded-xl p-2.5 text-center font-mono text-[11px] text-cyan-300 hover:text-white"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.maintainer@example.com')}
                className="glass-panel-interactive rounded-xl p-2.5 text-center font-mono text-[11px] text-amber-300 hover:text-white"
              >
                Maintainer
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.viewer@example.com')}
                className="glass-panel-interactive rounded-xl p-2.5 text-center font-mono text-[11px] text-slate-300 hover:text-white"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>

        {/* Footer Link */}
        <p className="text-center text-xs text-slate-400">
          Need an account?{' '}
          <Link to="/register" className="font-semibold text-cyan-400 hover:text-cyan-300 hover:underline">
            Submit registration request
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
