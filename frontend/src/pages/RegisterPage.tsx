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
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 p-4 font-sans selection:bg-cyan-500 selection:text-slate-950">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="space-y-2 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 font-bold text-slate-950 shadow-xl shadow-cyan-500/20">
            <Activity className="h-7 w-7 text-slate-950" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Request Platform Access</h1>
          <p className="font-mono text-xs text-slate-400">
            Public Registration (Requires Administrator Approval)
          </p>
        </div>

        {/* Card */}
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-2xl">
          {submitted ? (
            <div className="space-y-4 py-6 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-emerald-800 bg-emerald-950 text-emerald-400">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Request Submitted</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">
                  Your registration request is in{' '}
                  <span className="font-mono text-cyan-400">PENDING</span> status. A platform
                  administrator will review and grant role permissions before you can log in.
                </p>
              </div>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Return to Sign In
              </Link>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="flex items-center gap-2 rounded-lg border border-rose-800/60 bg-rose-950/80 p-3 font-mono text-xs text-rose-300">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="mb-1.5 block font-mono text-slate-400">Full Name</label>
                  <div className="relative">
                    <User className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pr-3 pl-9 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-mono text-slate-400">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@organization.com"
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
                      minLength={12}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="At least 12 characters"
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pr-3 pl-9 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block font-mono text-slate-400">
                    Organization / Facility Name (Optional)
                  </label>
                  <div className="relative">
                    <Building className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="Academic Motor Testing Lab"
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pr-3 pl-9 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 py-2.5 text-xs font-semibold text-white shadow-lg shadow-cyan-600/20 transition-all hover:bg-cyan-500 disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Access Request'}
                </button>
              </form>

              <p className="border-t border-slate-800/80 pt-2 text-center text-xs text-slate-400">
                Already registered?{' '}
                <Link to="/login" className="font-semibold text-cyan-400 hover:underline">
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
