import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock, RefreshCw, ShieldCheck, UserCheck } from 'lucide-react'
import { api } from '../lib/api'
import type { AuditLog, RegistrationRequest } from '../types/api'

export const AdminPage: React.FC = () => {
  const [auditActionFilter, setAuditActionFilter] = useState('all')
  const [banner, setBanner] = useState<string | null>(null)

  // Fetch Pending Registrations
  const { data: registrations = [], refetch: refetchRegistrations } = useQuery({
    queryKey: ['registrations'],
    queryFn: () => api.get<RegistrationRequest[]>('/admin/registrations?status=pending'),
  })

  // Fetch Audit Logs
  const { data: auditLogs = [], refetch: refetchAudits } = useQuery({
    queryKey: ['audit-logs', auditActionFilter],
    queryFn: () => {
      let q = '/audit-logs?limit=50'
      if (auditActionFilter !== 'all') q += `&action=${auditActionFilter}`
      return api.get<AuditLog[]>(q)
    },
  })

  const handleApprove = async (regId: string) => {
    try {
      await api.post(`/admin/registrations/${regId}/approve`, {
        initial_role: 'maintainer',
      })
      setBanner('User registration approved.')
      refetchRegistrations()
    } catch (err: any) {
      setBanner(`Approve failed: ${err.message}`)
    }
  }

  const handleReject = async (regId: string) => {
    try {
      await api.post(`/admin/registrations/${regId}/reject`)
      setBanner('User registration rejected.')
      refetchRegistrations()
    } catch (err: any) {
      setBanner(`Reject failed: ${err.message}`)
    }
  }

  return (
    <div className="space-y-6">
      {banner && (
        <div className="flex items-center justify-between rounded-lg border border-cyan-500/40 bg-cyan-950/80 p-3 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div>
        <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight text-white">
          <ShieldCheck className="h-5 w-5 text-cyan-400" />
          <span>System Administration & Audit Logs</span>
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Review pending user registration requests, manage role assignments, and inspect
          security-critical audit trails.
        </p>
      </div>

      {/* Pending Registrations Queue */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
          <UserCheck className="h-4 w-4 text-cyan-400" />
          Pending Account Approvals ({registrations.length})
        </h3>
        {registrations.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-800 p-8 text-center text-xs text-slate-500">
            No pending registration requests in queue.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 font-mono text-[10px] text-slate-400 uppercase">
                <tr>
                  <th className="p-3">Applicant Name</th>
                  <th className="p-3">Email Address</th>
                  <th className="p-3">Organization</th>
                  <th className="p-3">Submitted Date</th>
                  <th className="p-3 text-right">Approval Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {registrations.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40">
                    <td className="p-3 font-semibold text-white">{r.name}</td>
                    <td className="p-3 font-mono text-cyan-300">{r.email}</td>
                    <td className="p-3 text-slate-300">{r.organization_name || 'Academic Lab'}</td>
                    <td className="p-3 font-mono text-slate-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                    <td className="space-x-2 p-3 text-right">
                      <button
                        onClick={() => handleApprove(r.id)}
                        className="rounded border border-emerald-800 bg-emerald-950 px-3 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-900"
                      >
                        Approve (Maintainer)
                      </button>
                      <button
                        onClick={() => handleReject(r.id)}
                        className="rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-rose-400 hover:bg-slate-700"
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Logs Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
        <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
            <Clock className="h-4 w-4 text-cyan-400" />
            Security & Lifecycle Audit Trail
          </h3>
          <div className="flex items-center gap-2 text-xs">
            <select
              value={auditActionFilter}
              onChange={(e) => setAuditActionFilter(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 font-mono text-slate-300 focus:border-cyan-500 focus:outline-none"
            >
              <option value="all">All Actions</option>
              <option value="auth.login_succeeded">Logins</option>
              <option value="diagnosis.reviewed">Diagnosis Reviews</option>
              <option value="maintenance.created">Maintenance Created</option>
              <option value="file.uploaded">File Uploads</option>
              <option value="alert.resolved">Alert Resolutions</option>
            </select>
            <button
              onClick={() => refetchAudits()}
              className="rounded-lg bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 font-mono text-[10px] text-slate-400 uppercase">
              <tr>
                <th className="p-3">Action</th>
                <th className="p-3">Resource Type</th>
                <th className="p-3">Actor</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Event Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40">
                  <td className="p-3 font-semibold text-cyan-300">{log.action}</td>
                  <td className="p-3 text-slate-400 capitalize">{log.resource_type || 'system'}</td>
                  <td className="p-3 text-slate-300">{log.actor_name || 'System / Admin'}</td>
                  <td className="p-3 text-slate-500">
                    {new Date(log.created_at).toLocaleString([], {
                      dateStyle: 'short',
                      timeStyle: 'medium',
                    })}
                  </td>
                  <td className="max-w-xs truncate p-3 text-slate-400">
                    {log.metadata ? JSON.stringify(log.metadata) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AdminPage
