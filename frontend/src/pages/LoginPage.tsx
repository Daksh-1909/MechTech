import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, AlertCircle, ArrowRight, KeyRound, Lock, Mail, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export const LoginPage: React.FC = () => {
  const { login, error } = useAuth()
  const navigate = useNavigate()

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
      navigate('/')
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
      navigate('/')
    } catch (err: any) {
      setErrorMessage(err.message || 'Demo login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 selection:bg-cyan-500 selection:text-slate-950 font-sans">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold mx-auto shadow-xl shadow-cyan-500/20">
            <Activity className="w-7 h-7 text-slate-950" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sign in to MechTech</h1>
          <p className="text-xs text-slate-400 font-mono">
            Equipment Condition Monitoring & Diagnostics Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl space-y-5">
          {(errorMessage || error) && (
            <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800/60 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage || error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 font-mono mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 font-mono mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 disabled:opacity-50 transition-all text-xs"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="pt-4 border-t border-slate-800/80">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-2 text-center">
              Quick Demonstration Logins:
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.admin@example.com')}
                className="p-2 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono text-cyan-300 transition-colors"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.maintainer@example.com')}
                className="p-2 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono text-amber-300 transition-colors"
              >
                Maintainer
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('demo.viewer@example.com')}
                className="p-2 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono text-slate-300 transition-colors"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>

        {/* Footer Link */}
        <p className="text-center text-xs text-slate-400">
          Need an account?{' '}
          <Link to="/register" className="text-cyan-400 hover:underline font-semibold">
            Submit registration request
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage

