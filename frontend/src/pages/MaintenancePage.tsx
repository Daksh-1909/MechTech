import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Paperclip,
  Plus,
  ShieldCheck,
  Upload,
  UserCheck,
  Wrench,
  XCircle,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Alert, Diagnosis, Equipment, MaintenanceRecord } from '../types/api'

export const MaintenancePage: React.FC = () => {
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showVerifyModal, setShowVerifyModal] = useState(false)
  const [verificationStatus, setVerificationStatus] = useState<'verified' | 'rejected'>('verified')
  const [verificationNote, setVerificationNote] = useState('')
  const [banner, setBanner] = useState<string | null>(null)

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  // Fetch Work Orders
  const { data: records = [], refetch, isLoading } = useQuery({
    queryKey: ['maintenance-records'],
    queryFn: () => api.get<MaintenanceRecord[]>('/maintenance'),
  })

  // Fetch Equipment
  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  // Form State for Create
  const [title, setTitle] = useState('')
  const [equipmentId, setEquipmentId] = useState('')
  const [maintenanceType, setMaintenanceType] = useState('corrective')
  const [priority, setPriority] = useState('medium')
  const [description, setDescription] = useState('')

  const activeRecord =
    records.find((r) => r.id === selectedRecordId) || records[0]

  const handleCreateWorkOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    const targetEq = equipmentId || equipment[0]?.id
    if (!targetEq) return
    try {
      const res = await api.post<MaintenanceRecord>('/maintenance', {
        title,
        equipment_id: targetEq,
        maintenance_type: maintenanceType,
        priority,
        description,
        status: 'scheduled',
      })
      setShowCreateModal(false)
      setTitle('')
      setDescription('')
      setBanner(`Work order created: ${res.title}`)
      await refetch()
      setSelectedRecordId(res.id)
    } catch (err: any) {
      setBanner(`Failed to create work order: ${err.message}`)
    }
  }

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeRecord) return
    try {
      await api.post(`/maintenance/${activeRecord.id}/verify`, {
        verification_status: verificationStatus,
        verification_note: verificationNote || 'Work order inspected and confirmed.',
      })
      setShowVerifyModal(false)
      setVerificationNote('')
      setBanner(`Work order marked ${verificationStatus.toUpperCase()}.`)
      refetch()
    } catch (err: any) {
      setBanner(`Verification failed: ${err.message}`)
    }
  }

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeRecord || !uploadFile) return
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('purpose', 'maintenance_attachment')

      await api.upload(`/maintenance/${activeRecord.id}/attachments`, formData)
      setUploadFile(null)
      setBanner(`Attachment '${uploadFile.name}' uploaded successfully.`)
      refetch()
    } catch (err: any) {
      setBanner(`File upload failed: ${err.message}`)
    } finally {
      setIsUploading(false)
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

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Maintenance Work Orders & File Attachments</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Track corrective repairs, link diagnostic findings, upload inspection documentation, and record supervisor verification.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-cyan-600/20"
        >
          <Plus className="w-4 h-4" />
          Create Work Order
        </button>
      </div>

      {/* Main Grid: Orders List & Detailed Inspection Work Order View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Work Orders List */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">
            Orders Queue ({records.length})
          </h3>
          <div className="space-y-2 overflow-y-auto max-h-[620px] pr-1">
            {records.map((r) => {
              const isSelected = activeRecord?.id === r.id
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRecordId(r.id)}
                  className={`p-3.5 rounded-lg border text-left cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-cyan-950/40 border-cyan-500/60 shadow-md'
                      : 'bg-slate-950/50 border-slate-800 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-bold ${
                        r.priority === 'critical'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : r.priority === 'high'
                            ? 'bg-amber-950 text-amber-400 border border-amber-800'
                            : 'bg-blue-950 text-blue-400 border border-blue-800'
                      }`}
                    >
                      {r.priority}
                    </span>
                    <span
                      className={`text-[10px] font-mono capitalize ${
                        r.verification_status === 'verified' ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    >
                      {r.verification_status}
                    </span>
                  </div>

                  <h4 className="font-semibold text-white text-xs tracking-tight line-clamp-1">{r.title}</h4>
                  <div className="text-[11px] text-slate-400 font-mono mt-2 flex items-center justify-between">
                    <span>{r.equipment_asset_tag || 'DEMO-MTR-001'}</span>
                    <span className="capitalize">{r.status.replace('_', ' ')}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right 2 Cols: Work Order Detail & Attachment Uploader */}
        <div className="lg:col-span-2 space-y-5">
          {activeRecord ? (
            <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-5">
              {/* Top Overview & Verification Status */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-mono uppercase bg-slate-800 text-slate-300 font-semibold">
                      {activeRecord.maintenance_type}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Asset: {activeRecord.equipment_asset_tag || activeRecord.equipment_name || 'Electric Motor'}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1.5">{activeRecord.title}</h3>
                  {activeRecord.description && (
                    <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                      {activeRecord.description}
                    </p>
                  )}
                </div>

                {/* Verification Action */}
                <div>
                  {activeRecord.verification_status === 'pending' ? (
                    <button
                      onClick={() => setShowVerifyModal(true)}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      Verify Completion
                    </button>
                  ) : (
                    <div className="text-right">
                      <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-mono font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        VERIFIED BY SUPERVISOR
                      </span>
                      {activeRecord.verification_note && (
                        <div className="text-[11px] text-slate-400 font-mono mt-1">
                          "{activeRecord.verification_note}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Maintenance Details */}
              <div className="grid grid-cols-2 gap-4 text-xs font-mono bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Work Order Status</span>
                  <span className="text-white font-semibold capitalize">{activeRecord.status.replace('_', ' ')}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Outcome</span>
                  <span className="text-emerald-400 font-semibold capitalize">{activeRecord.outcome.replace('_', ' ')}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Created Date</span>
                  <span className="text-slate-300">{new Date(activeRecord.created_at).toLocaleDateString()}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Notes / Instructions</span>
                  <span className="text-slate-300">{activeRecord.notes || 'Nominal maintenance standards.'}</span>
                </div>
              </div>

              {/* File Attachments Section */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    <Paperclip className="w-4 h-4 text-cyan-400" />
                    Inspection Photos & PDF Documentation ({activeRecord.attachments?.length || 0})
                  </h4>
                </div>

                {/* Upload Form */}
                <form
                  onSubmit={handleFileUpload}
                  className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs"
                >
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700"
                  />
                  <button
                    type="submit"
                    disabled={!uploadFile || isUploading}
                    className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    {isUploading ? 'Uploading...' : 'Upload Document'}
                  </button>
                </form>

                {/* Existing Attachments List */}
                {activeRecord.attachments && activeRecord.attachments.length > 0 ? (
                  <div className="space-y-2">
                    {activeRecord.attachments.map((f) => (
                      <div
                        key={f.id}
                        className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2.5 truncate pr-3">
                          <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
                          <div>
                            <span className="text-slate-200 font-semibold block truncate">
                              {f.original_filename}
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono">
                              {(f.size_bytes / 1024).toFixed(1)} KB • SHA: {f.checksum.slice(0, 10)}...
                            </span>
                          </div>
                        </div>

                        <a
                          href={`/api/v1/files/${f.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 font-mono text-[11px] flex items-center gap-1.5"
                        >
                          <Download className="w-3 h-3" />
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
                    No files or inspection photos attached yet.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
              Select or create a work order to review task execution and documentation.
            </div>
          )}
        </div>
      </div>

      {/* Create Work Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Create Maintenance Work Order</h3>
            <form onSubmit={handleCreateWorkOrder} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Work Order Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Drive-End Front Bearing Replacement"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-mono mb-1">Equipment</label>
                <select
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                >
                  {equipment.map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.asset_tag} — {eq.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Type</label>
                  <select
                    value={maintenanceType}
                    onChange={(e) => setMaintenanceType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="corrective">Corrective</option>
                    <option value="preventive">Preventive</option>
                    <option value="condition_based">Condition Based</option>
                    <option value="emergency">Emergency</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-mono mb-1">Description & Tasks</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Task scope, replacement parts, and safety lockout requirements..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold"
                >
                  Submit Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verify Modal */}
      {showVerifyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Technician / Supervisor Verification</h3>
            <form onSubmit={handleVerifySubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Verification Status</label>
                <select
                  value={verificationStatus}
                  onChange={(e: any) => setVerificationStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="verified">Verified (Task completed and inspected)</option>
                  <option value="rejected">Rejected (Rework required)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-mono mb-1">Verification Note</label>
                <textarea
                  required
                  rows={3}
                  value={verificationNote}
                  onChange={(e) => setVerificationNote(e.target.value)}
                  placeholder="e.g. Clearance measured at 0.045mm within manufacturer specification. Unit run-tested for 30 minutes nominal."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowVerifyModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold"
                >
                  Confirm Verification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default MaintenancePage

