import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, AlertCircle, ArrowLeft, CheckCircle2, Lock, Mail, User, Building } from 'lucide-react'
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
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 selection:bg-cyan-500 selection:text-slate-950 font-sans">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold mx-auto shadow-xl shadow-cyan-500/20">
            <Activity className="w-7 h-7 text-slate-950" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Request Platform Access</h1>
          <p className="text-xs text-slate-400 font-mono">
            Public Registration (Requires Administrator Approval)
          </p>
        </div>

        {/* Card */}
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl space-y-5">
          {submitted ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-950 border border-emerald-800 flex items-center justify-center mx-auto text-emerald-400">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Request Submitted</h3>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  Your registration request is in <span className="text-cyan-400 font-mono">PENDING</span> status. A platform administrator will review and grant role permissions before you can log in.
                </p>
              </div>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Return to Sign In
              </Link>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800/60 text-rose-300 text-xs font-mono flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-400 font-mono mb-1.5">Full Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 font-mono mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@organization.com"
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
                      minLength={8}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 8 characters"
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 font-mono mb-1.5">Organization / Facility Name (Optional)</label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="Academic Motor Testing Lab"
                      className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-xs"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 disabled:opacity-50 transition-all text-xs"
                >
                  {loading ? 'Submitting...' : 'Submit Access Request'}
                </button>
              </form>

              <p className="text-center text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                Already registered?{' '}
                <Link to="/login" className="text-cyan-400 hover:underline font-semibold">
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

