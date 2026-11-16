import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Activity, AlertCircle, ArrowRight, Lock, Mail } from 'lucide-react'
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
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 p-4 font-sans selection:bg-cyan-500 selection:text-slate-950">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 font-bold text-slate-950 shadow-xl shadow-cyan-500/20">
            <Activity className="h-7 w-7 text-slate-950" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Sign in to MechTech</h1>
          <p className="font-mono text-xs text-slate-400">
            Equipment Condition Monitoring & Diagnostics Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-2xl">
          {(errorMessage || error) && (
            <div className="flex items-center gap-2 rounded-lg border border-rose-800/60 bg-rose-950/80 p-3 font-mono text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage || error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="mb-1.5 block font-mono text-slate-400">Email Address</label>
              <div className="relative">
                <Mail className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pr-3 pl-9 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block font-mono text-slate-400">Password</label>
              <div className="relative">
                <Lock className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pr-3 pl-9 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 py-2.5 text-xs font-semibold text-white shadow-lg shadow-cyan-600/20 transition-all hover:bg-cyan-500 disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="border-t border-slate-800/80 pt-4">
            <span className="mb-2 block text-center font-mono text-[10px] tracking-wider text-slate-400 uppercase">
              Quick Demonstration Logins:
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.admin@example.com')}
                className="rounded border border-slate-800 bg-slate-950 p-2 font-mono text-[11px] text-cyan-300 transition-colors hover:bg-slate-800"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.maintainer@example.com')}
                className="rounded border border-slate-800 bg-slate-950 p-2 font-mono text-[11px] text-amber-300 transition-colors hover:bg-slate-800"
              >
                Maintainer
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.viewer@example.com')}
                className="rounded border border-slate-800 bg-slate-950 p-2 font-mono text-[11px] text-slate-300 transition-colors hover:bg-slate-800"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>

        {/* Footer Link */}
        <p className="text-center text-xs text-slate-400">
          Need an account?{' '}
          <Link to="/register" className="font-semibold text-cyan-400 hover:underline">
            Submit registration request
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
