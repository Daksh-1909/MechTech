import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { api } from '../lib/api'
import type { Alert } from '../types/api'

export const AlertsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [resolvingAlert, setResolvingAlert] = useState<Alert | null>(null)
  const [resolutionNote, setResolutionNote] = useState('')
  const [banner, setBanner] = useState<string | null>(null)

  const {
    data: alerts = [],
    isLoading,
    refetch,
  } = useQuery({
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
        <div className="flex items-center justify-between rounded-lg border border-cyan-500/40 bg-cyan-950/80 p-3 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">
            ✕
          </button>
        </div>
      )}

      {/* Header & Filter Controls */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Active Anomaly Alerts</h2>
          <p className="mt-1 text-xs text-slate-400">
            Real-time threshold breaches, statistical sensor anomalies, and equipment warnings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
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
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button
            onClick={() => refetch()}
            className="rounded-lg border border-slate-800 bg-slate-900 p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      {isLoading ? (
        <div className="p-12 text-center font-mono text-sm text-slate-400">Loading alerts...</div>
      ) : alerts.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-12 text-center text-sm text-slate-400">
          No alerts found matching filter criteria. Fleet condition is nominal.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/90 shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 font-mono text-[10px] text-slate-400 uppercase">
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
                        className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold uppercase ${
                          a.severity === 'critical'
                            ? 'border border-rose-800 bg-rose-950 text-rose-400'
                            : a.severity === 'high'
                              ? 'border border-amber-800 bg-amber-950 text-amber-400'
                              : 'border border-blue-800 bg-blue-950 text-blue-400'
                        }`}
                      >
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <div className="font-semibold text-white">{a.title}</div>
                      {a.description && (
                        <div className="mt-0.5 text-[11px] text-slate-400">{a.description}</div>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-slate-300">
                      {a.equipment_asset_tag || a.equipment_id.slice(0, 8)}
                    </td>
                    <td className="p-3.5">
                      <span
                        className={`font-mono text-[11px] font-semibold capitalize ${
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
                      {new Date(a.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="p-3.5 text-right">
                      {a.status === 'open' && (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-slate-200 hover:bg-slate-700"
                          >
                            Acknowledge
                          </button>
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="rounded border border-emerald-800/60 bg-emerald-950 px-2.5 py-1 font-semibold text-emerald-300 hover:bg-emerald-900"
                          >
                            Resolve
                          </button>
                        </div>
                      )}
                      {a.status === 'acknowledged' && (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="rounded border border-emerald-800/60 bg-emerald-950 px-2.5 py-1 font-semibold text-emerald-300 hover:bg-emerald-900"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleDismiss(a.id)}
                            className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-slate-400 hover:bg-slate-700"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                      {(a.status === 'resolved' || a.status === 'dismissed') && (
                        <span className="font-mono text-[11px] text-slate-500">
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white">Resolve Anomaly Alert</h3>
            <p className="text-xs text-slate-400">
              Provide a resolution note detailing corrective actions taken (e.g. grease replenished,
              load reduced).
            </p>
            <form onSubmit={handleResolve} className="space-y-3 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-400">Resolution Note</label>
                <textarea
                  required
                  rows={3}
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="e.g. Bearing cavity inspected and replenished with 40g ISO VG 46 synthetic lubricant."
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResolvingAlert(null)}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-500"
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
