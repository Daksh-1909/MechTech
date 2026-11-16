import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock, RefreshCw, ShieldCheck, UserCheck, X } from 'lucide-react'
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
        <div className="glass-panel flex items-center justify-between border-cyan-500/40 bg-cyan-950/40 p-3.5 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div>
        <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight text-white drop-shadow-sm">
          <ShieldCheck className="h-5 w-5 text-cyan-400" />
          <span>System Administration & Audit Logs</span>
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Review pending user registration requests, manage role assignments, and inspect
          security-critical audit trails.
        </p>
      </div>

      {/* Pending Registrations Queue */}
      <div className="glass-panel overflow-hidden p-6 shadow-xl">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
          <UserCheck className="h-4 w-4 text-cyan-400" />
          Pending Account Approvals ({registrations.length})
        </h3>
        {registrations.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 p-8 text-center text-xs text-slate-400">
            No pending registration requests in queue.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/5 bg-slate-950/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/5 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Applicant Name</th>
                  <th className="p-3.5">Email Address</th>
                  <th className="p-3.5">Organization</th>
                  <th className="p-3.5">Submitted Date</th>
                  <th className="p-3.5 text-right">Approval Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {registrations.map((r) => (
                  <tr key={r.id} className="transition-colors hover:bg-white/[0.04]">
                    <td className="p-3.5 font-semibold text-white">{r.name}</td>
                    <td className="p-3.5 font-mono text-cyan-300">{r.email}</td>
                    <td className="p-3.5 text-slate-300">{r.organization_name || 'Academic Lab'}</td>
                    <td className="p-3.5 font-mono text-slate-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleApprove(r.id)}
                          className="glass-btn-emerald px-3 py-1 font-semibold"
                        >
                          Approve (Maintainer)
                        </button>
                        <button
                          onClick={() => handleReject(r.id)}
                          className="glass-btn px-3 py-1 text-slate-400 hover:text-rose-400"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Logs Trail */}
      <div className="glass-panel overflow-hidden p-6 shadow-xl">
        <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Immutable Audit Trail</h3>
          </div>

          <div className="flex items-center gap-2.5">
            <select
              value={auditActionFilter}
              onChange={(e) => setAuditActionFilter(e.target.value)}
              className="glass-input text-xs"
            >
              <option value="all">All Actions</option>
              <option value="auth.login">auth.login</option>
              <option value="auth.register">auth.register</option>
              <option value="telemetry.batch_ingest">telemetry.batch_ingest</option>
              <option value="diagnostics.generate">diagnostics.generate</option>
              <option value="maintenance.create">maintenance.create</option>
            </select>

            <button
              onClick={() => refetchAudits()}
              className="glass-panel-interactive flex h-9 w-9 items-center justify-center rounded-xl text-slate-300 hover:text-white"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/5 bg-slate-950/40">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/5 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">Action</th>
                <th className="p-3.5">Target Entity</th>
                <th className="p-3.5">IP Address</th>
                <th className="p-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {auditLogs.map((log) => (
                <tr key={log.id} className="transition-colors hover:bg-white/[0.04]">
                  <td className="p-3.5 text-slate-400">
                    {new Date(log.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </td>
                  <td className="p-3.5 font-semibold text-cyan-300">{log.action}</td>
                  <td className="p-3.5 text-slate-300">
                    {log.target_type ? `${log.target_type}:${log.target_id?.slice(0, 8)}` : '—'}
                  </td>
                  <td className="p-3.5 text-slate-400">{log.ip_address || '127.0.0.1'}</td>
                  <td className="p-3.5">
                    <span className="glass-pill glass-pill-emerald text-[10px]">
                      SUCCESS
                    </span>
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
