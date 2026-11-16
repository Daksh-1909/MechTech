import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Lock,
  Mail,
  User,
  Building,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export const RegisterPage: React.FC = () => {
  const { register } = useAuth()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [orgName, setOrgName] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorMessage(null)
    try {
      await register(name, email, password, orgName || undefined)
      setSubmitted(true)
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration submission failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-slate-950 p-4 font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Floating Apple Liquid Mesh Aurora Orbs */}
      <div className="liquid-glow-orb-cyan pointer-events-none" />
      <div className="liquid-glow-orb-indigo pointer-events-none" />
      <div className="liquid-glow-orb-emerald pointer-events-none" />

      <div className="relative z-10 w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="space-y-3 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 font-bold text-slate-950 shadow-2xl shadow-cyan-500/30 transition-transform duration-500 hover:scale-105">
            <Activity className="h-8 w-8 text-slate-950" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white drop-shadow-md">
              Request Platform Access
            </h1>
            <p className="mt-1 font-mono text-xs text-slate-400">
              Public Registration (Requires Administrator Approval)
            </p>
          </div>
        </div>

        {/* Apple Liquid Glass Card */}
        <div className="glass-panel space-y-5 p-8 shadow-2xl">
          {submitted ? (
            <div className="space-y-4 py-6 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-400/40 bg-emerald-500/20 text-emerald-400 shadow-xl shadow-emerald-500/20">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Access Request Submitted</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-300">
                  Your registration request is in{' '}
                  <span className="glass-pill glass-pill-cyan font-mono text-[11px]">PENDING</span>{' '}
                  status. A platform administrator will review and grant role permissions before you can
                  sign in.
                </p>
              </div>
              <div className="pt-2">
                <Link
                  to="/login"
                  className="glass-btn inline-flex items-center gap-1.5 px-4 py-2 font-mono text-xs text-cyan-300 hover:text-white"
                >
                  <ArrowLeft className="h-3.5 w-3.5" /> Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="glass-panel flex items-center gap-2.5 border-rose-500/40 bg-rose-950/40 p-3.5 font-mono text-xs text-rose-300">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="mb-1.5 block font-mono text-slate-300">Full Name</label>
                  <div className="relative">
                    <User className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="glass-input w-full pl-10"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-mono text-slate-300">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@organization.com"
                      className="glass-input w-full pl-10"
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
                      minLength={12}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="At least 12 characters"
                      className="glass-input w-full pl-10"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-mono text-slate-300">
                    Organization / Facility Name (Optional)
                  </label>
                  <div className="relative">
                    <Building className="absolute top-2.5 left-3.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="Academic Motor Testing Lab"
                      className="glass-input w-full pl-10"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="glass-btn-primary flex w-full items-center justify-center gap-2 py-3 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Access Request'}
                </button>
              </form>

              <p className="border-t border-white/10 pt-3 text-center text-xs text-slate-400">
                Already registered?{' '}
                <Link to="/login" className="font-semibold text-cyan-400 hover:text-cyan-300 hover:underline">
                  Sign in here
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
