import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, X, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react'
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
        <div className="glass-panel flex items-center justify-between border-cyan-500/40 bg-cyan-950/40 p-3.5 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header & Filter Controls */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white drop-shadow-sm">
            Active Anomaly Alerts
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Real-time threshold breaches, statistical sensor anomalies, and equipment warnings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="glass-input text-xs"
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
            className="glass-input text-xs"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button
            onClick={() => refetch()}
            className="glass-panel-interactive flex h-9 w-9 items-center justify-center rounded-xl text-slate-300 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      {isLoading ? (
        <div className="glass-panel p-16 text-center font-mono text-sm text-slate-400">
          Loading alerts...
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-panel p-16 text-center">
          <CheckCircle2 className="mx-auto mb-3 h-8 w-8 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Fleet Operating Nominally</h3>
          <p className="mt-1 text-xs text-slate-400">
            No anomaly alerts found matching filter criteria.
          </p>
        </div>
      ) : (
        <div className="glass-panel overflow-hidden p-6 shadow-2xl">
          <div className="overflow-x-auto rounded-xl border border-white/5 bg-slate-950/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/5 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Alert Title</th>
                  <th className="p-3.5">Equipment</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Detected At</th>
                  <th className="p-3.5 text-right">Triage Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {alerts.map((a) => (
                  <tr key={a.id} className="transition-colors hover:bg-white/[0.04]">
                    <td className="p-3.5">
                      <span
                        className={`glass-pill text-[10px] font-mono uppercase ${
                          a.severity === 'critical'
                            ? 'glass-pill-critical'
                            : a.severity === 'high'
                              ? 'glass-pill-warning'
                              : 'glass-pill-cyan'
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
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="glass-btn px-2.5 py-1 text-slate-300 hover:text-white"
                          >
                            Acknowledge
                          </button>
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="glass-btn-emerald px-2.5 py-1 font-semibold"
                          >
                            Resolve
                          </button>
                        </div>
                      )}
                      {a.status === 'acknowledged' && (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setResolvingAlert(a)}
                            className="glass-btn-emerald px-2.5 py-1 font-semibold"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleDismiss(a.id)}
                            className="glass-btn px-2.5 py-1 text-slate-400 hover:text-white"
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

      {/* Resolve Modal (Apple Frosted Glass Sheet) */}
      {resolvingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md space-y-4 p-6 shadow-2xl border-white/15 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Resolve Anomaly Alert</h3>
              <button
                onClick={() => setResolvingAlert(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Provide a resolution note detailing corrective actions taken (e.g. grease replenished,
              load reduced).
            </p>
            <form onSubmit={handleResolve} className="space-y-3.5 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-300">Resolution Note</label>
                <textarea
                  required
                  rows={3}
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="e.g. Bearing cavity inspected and replenished with 40g ISO VG 46 synthetic lubricant."
                  className="glass-input w-full"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setResolvingAlert(null)}
                  className="glass-btn px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="glass-btn-emerald px-4 py-2 font-semibold text-white"
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
