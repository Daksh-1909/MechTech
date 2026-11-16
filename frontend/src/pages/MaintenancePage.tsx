import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle2,
  Download,
  FileText,
  Paperclip,
  Plus,
  ShieldCheck,
  Upload,
  X,
  Wrench,
  Clock,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Equipment, MaintenanceRecord } from '../types/api'

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
  const { data: records = [], refetch } = useQuery({
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

  const activeRecord = records.find((r) => r.id === selectedRecordId) || records[0]

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
        <div className="glass-panel flex items-center justify-between border-cyan-500/40 bg-cyan-950/40 p-3.5 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight text-white drop-shadow-sm">
            <span>Maintenance Work Orders & File Attachments</span>
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Track corrective repairs, link diagnostic findings, upload inspection documentation, and
            record supervisor verification.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="glass-btn-primary flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white"
        >
          <Plus className="h-4 w-4" />
          Create Work Order
        </button>
      </div>

      {/* Main Grid: Orders List & Detailed Inspection Work Order View */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Col: Work Orders List */}
        <div className="glass-panel p-5 shadow-xl">
          <h3 className="mb-3.5 font-mono text-xs tracking-wider text-slate-400 uppercase">
            Orders Queue ({records.length})
          </h3>
          <div className="max-h-[620px] space-y-2.5 overflow-y-auto pr-1">
            {records.map((r) => {
              const isSelected = activeRecord?.id === r.id
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRecordId(r.id)}
                  className={`glass-panel-interactive cursor-pointer rounded-xl p-3.5 text-left transition-all ${
                    isSelected
                      ? 'border-cyan-400/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10'
                      : 'border-white/5 bg-slate-950/40'
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span
                      className={`glass-pill text-[10px] font-bold uppercase font-mono ${
                        r.priority === 'critical'
                          ? 'glass-pill-critical'
                          : r.priority === 'high'
                            ? 'glass-pill-warning'
                            : 'glass-pill-cyan'
                      }`}
                    >
                      {r.priority}
                    </span>
                    <span
                      className={`font-mono text-[10px] capitalize ${
                        r.verification_status === 'verified' ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    >
                      {r.verification_status}
                    </span>
                  </div>

                  <h4 className="line-clamp-1 text-xs font-semibold tracking-tight text-white">
                    {r.title}
                  </h4>
                  <div className="mt-2.5 flex items-center justify-between font-mono text-[11px] text-slate-400">
                    <span>{r.equipment_asset_tag || 'DEMO-MTR-001'}</span>
                    <span className="capitalize">{r.status.replace('_', ' ')}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right 2 Cols: Work Order Detail & Attachment Uploader */}
        <div className="space-y-5 lg:col-span-2">
          {activeRecord ? (
            <div className="glass-panel space-y-5 p-6 shadow-2xl">
              {/* Top Overview & Verification Status */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="glass-pill font-mono text-xs font-semibold text-slate-300 uppercase">
                      {activeRecord.maintenance_type}
                    </span>
                    <span className="font-mono text-xs text-slate-400">
                      Asset:{' '}
                      {activeRecord.equipment_asset_tag ||
                        activeRecord.equipment_name ||
                        'Electric Motor'}
                    </span>
                  </div>
                  <h3 className="mt-2 text-lg font-bold text-white">{activeRecord.title}</h3>
                  {activeRecord.description && (
                    <p className="mt-1 max-w-xl text-xs leading-relaxed text-slate-300">
                      {activeRecord.description}
                    </p>
                  )}
                </div>

                {/* Verification Action */}
                <div>
                  {activeRecord.verification_status === 'pending' ? (
                    <button
                      onClick={() => setShowVerifyModal(true)}
                      className="glass-btn-emerald flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      Verify Completion
                    </button>
                  ) : (
                    <div className="text-right">
                      <span className="glass-pill glass-pill-emerald flex items-center gap-1.5 text-xs font-bold">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        VERIFIED BY SUPERVISOR
                      </span>
                      {activeRecord.verification_note && (
                        <div className="mt-1 font-mono text-[11px] text-slate-400">
                          "{activeRecord.verification_note}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Maintenance Details */}
              <div className="grid grid-cols-2 gap-4 rounded-xl border border-white/5 bg-slate-950/40 p-4 font-mono text-xs">
                <div>
                  <span className="block text-[10px] text-slate-400 uppercase tracking-wider">
                    Work Order Status
                  </span>
                  <span className="font-semibold text-white capitalize">
                    {activeRecord.status.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400 uppercase tracking-wider">Outcome</span>
                  <span className="font-semibold text-emerald-400 capitalize">
                    {activeRecord.outcome.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400 uppercase tracking-wider">Created Date</span>
                  <span className="text-slate-300">
                    {new Date(activeRecord.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400 uppercase tracking-wider">
                    Notes / Instructions
                  </span>
                  <span className="text-slate-300">
                    {activeRecord.notes || 'Nominal maintenance standards.'}
                  </span>
                </div>
              </div>

              {/* File Attachments Section */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h4 className="flex items-center gap-2 text-xs font-bold tracking-wider text-slate-200 uppercase">
                    <Paperclip className="h-4 w-4 text-cyan-400" />
                    Inspection Photos & PDF Documentation ({activeRecord.attachments?.length || 0})
                  </h4>
                </div>

                {/* Upload Form */}
                <form
                  onSubmit={handleFileUpload}
                  className="glass-panel-interactive flex flex-wrap items-center justify-between gap-3 rounded-xl border-white/5 bg-slate-950/40 p-4 text-xs"
                >
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-200 hover:file:bg-white/20 file:transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!uploadFile || isUploading}
                    className="glass-btn-primary flex items-center gap-1.5 px-4 py-2 font-semibold text-white disabled:opacity-50"
                  >
                    <Upload className="h-3.5 w-3.5" />
                    {isUploading ? 'Uploading...' : 'Upload Document'}
                  </button>
                </form>

                {/* Existing Attachments List */}
                {activeRecord.attachments && activeRecord.attachments.length > 0 ? (
                  <div className="space-y-2">
                    {activeRecord.attachments.map((f) => (
                      <div
                        key={f.id}
                        className="glass-panel-interactive flex items-center justify-between rounded-xl border-white/5 bg-slate-950/40 p-3.5 text-xs"
                      >
                        <div className="flex items-center gap-3 truncate pr-3">
                          <FileText className="h-4 w-4 shrink-0 text-cyan-400" />
                          <div>
                            <span className="block truncate font-semibold text-slate-200">
                              {f.original_filename}
                            </span>
                            <span className="font-mono text-[10px] text-slate-400">
                              {(f.size_bytes / 1024).toFixed(1)} KB • SHA: {f.checksum.slice(0, 10)}
                              ...
                            </span>
                          </div>
                        </div>

                        <a
                          href={`/api/v1/files/${f.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="glass-btn flex items-center gap-1.5 px-3 py-1 font-mono text-[11px] text-cyan-300 hover:text-white"
                        >
                          <Download className="h-3 w-3" />
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-white/10 p-6 text-center text-xs text-slate-400">
                    No files or inspection photos attached yet.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-panel p-16 text-center text-sm text-slate-400">
              Select or create a work order to review task execution and documentation.
            </div>
          )}
        </div>
      </div>

      {/* Create Work Order Modal (Apple Frosted Glass Sheet) */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md space-y-4 p-6 shadow-2xl border-white/15 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Create Maintenance Work Order</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateWorkOrder} className="space-y-3.5 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-300">Work Order Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Drive-End Front Bearing Replacement"
                  className="glass-input w-full"
                />
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-300">Equipment</label>
                <select
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  className="glass-input w-full"
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
                  <label className="mb-1 block font-mono text-slate-300">Type</label>
                  <select
                    value={maintenanceType}
                    onChange={(e) => setMaintenanceType(e.target.value)}
                    className="glass-input w-full"
                  >
                    <option value="corrective">Corrective</option>
                    <option value="preventive">Preventive</option>
                    <option value="condition_based">Condition Based</option>
                    <option value="emergency">Emergency</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-mono text-slate-300">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="glass-input w-full"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-300">Description & Tasks</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Task scope, replacement parts, and safety lockout requirements..."
                  className="glass-input w-full"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="glass-btn px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="glass-btn-primary px-4 py-2 font-semibold text-white"
                >
                  Submit Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verify Modal (Apple Frosted Glass Sheet) */}
      {showVerifyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md space-y-4 p-6 shadow-2xl border-white/15 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Technician / Supervisor Verification</h3>
              <button
                onClick={() => setShowVerifyModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleVerifySubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-300">Verification Status</label>
                <select
                  value={verificationStatus}
                  onChange={(e: any) => setVerificationStatus(e.target.value)}
                  className="glass-input w-full"
                >
                  <option value="verified">Verified (Task completed and inspected)</option>
                  <option value="rejected">Rejected (Rework required)</option>
                </select>
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-300">Verification Note</label>
                <textarea
                  required
                  rows={3}
                  value={verificationNote}
                  onChange={(e) => setVerificationNote(e.target.value)}
                  placeholder="e.g. Clearance measured at 0.045mm within manufacturer specification. Unit run-tested for 30 minutes nominal."
                  className="glass-input w-full"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowVerifyModal(false)}
                  className="glass-btn px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="glass-btn-emerald px-4 py-2 font-semibold text-white"
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
