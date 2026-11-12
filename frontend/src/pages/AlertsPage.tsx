import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  Search,
  ShieldAlert,
  XCircle,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Alert } from '../types/api'

export const AlertsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [resolvingAlert, setResolvingAlert] = useState<Alert | null>(null)
  const [resolutionNote, setResolutionNote] = useState('')
  const [banner, setBanner] = useState<string | null>(null)

  const { data: alerts = [], isLoading, refetch } = useQuery({
    queryKey: ['alerts', statusFilter, severityFilter],
    queryFn: () => {
      let q = '/alerts?'
      if (statusFilter !== 'all') q += `status=${statusFilter}&`
      if (severityFilter !== 'all') q += `severity=${severityFilter}&`
      return api.get<Alert[]>(q)
    },
  })

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/acknowledge`)
      setBanner('Alert acknowledged.')
      refetch()
    } catch (err: any) {
      setBanner(`Acknowledge failed: ${err.message}`)
    }
  }

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!resolvingAlert) return
    try {
      await api.post(`/alerts/${resolvingAlert.id}/resolve`, {
        resolution_note: resolutionNote || 'Resolved by maintainer.',
      })
      setResolvingAlert(null)
      setResolutionNote('')
      setBanner('Alert resolved successfully.')
      refetch()
    } catch (err: any) {
      setBanner(`Resolve failed: ${err.message}`)
    }
  }

  const handleDismiss = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/dismiss`)
      setBanner('Alert dismissed.')
      refetch()
    } catch (err: any) {
      setBanner(`Dismiss failed: ${err.message}`)
    }
  }

  return (
    <div className="space-y-6">
      {banner && (
        <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-200 text-xs font-mono flex items-center justify-between">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">✕</button>
        </div>
      )}

      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Active Anomaly Alerts</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time threshold breaches, statistical sensor anomalies, and equipment warnings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button
            onClick={() => refetch()}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 font-mono text-sm">Loading alerts...</div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
          No alerts found matching filter criteria. Fleet condition is nominal.
        </div>
      ) : (
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Alert Title</th>
                  <th className="p-3.5">Equipment</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Detected At</th>
                  <th className="p-3.5 text-right">Triage Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {alerts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/40">
                    <td className="p-3.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                          a.severity === 'critical'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : a.severity === 'high'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-blue-950 text-blue-400 border border-blue-800'
                        }`}
                      >
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <div className="font-semibold text-white">{a.title}</div>
                      {a.description && <div className="text-[11px] text-slate-400 mt-0.5">{a.description}</div>}
                    </td>
                    <td className="p-3.5 font-mono text-slate-300">
                      {a.equipment_asset_tag || a.equipment_id.slice(0, 8)}
                    </td>
                    <td className="p-3.5">
                      <span
                        className={`capitalize font-mono text-[11px] font-semibold ${
                          a.status === 'open'
                            ? 'text-rose-400'
                            : a.status === 'acknowledged'
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                        }`}
                      >
                        {a.status}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-400">
                      {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="p-3.5 text-right">
                      {a.status === 'open' && (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                          >
                            Acknowledge
                          </button>
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/60 font-semibold"
                          >
                            Resolve
                          </button>
                        </div>
                      )}
                      {a.status === 'acknowledged' && (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/60 font-semibold"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleDismiss(a.id)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                      {(a.status === 'resolved' || a.status === 'dismissed') && (
                        <span className="text-[11px] text-slate-500 font-mono">
                          {a.resolution_note || 'Closed'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {resolvingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Resolve Anomaly Alert</h3>
            <p className="text-xs text-slate-400">
              Provide a resolution note detailing corrective actions taken (e.g. grease replenished, load reduced).
            </p>
            <form onSubmit={handleResolve} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Resolution Note</label>
                <textarea
                  required
                  rows={3}
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="e.g. Bearing cavity inspected and replenished with 40g ISO VG 46 synthetic lubricant."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResolvingAlert(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold"
                >
                  Confirm Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AlertsPage

