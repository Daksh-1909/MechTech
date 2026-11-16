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
        <div className="flex items-center justify-between rounded-lg border border-cyan-500/40 bg-cyan-950/80 p-3 font-mono text-xs text-cyan-200">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight text-white">
            <span>Maintenance Work Orders & File Attachments</span>
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Track corrective repairs, link diagnostic findings, upload inspection documentation, and
            record supervisor verification.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-600/20 hover:bg-cyan-500"
        >
          <Plus className="h-4 w-4" />
          Create Work Order
        </button>
      </div>

      {/* Main Grid: Orders List & Detailed Inspection Work Order View */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Col: Work Orders List */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-xl">
          <h3 className="mb-3 font-mono text-xs tracking-wider text-slate-400 uppercase">
            Orders Queue ({records.length})
          </h3>
          <div className="max-h-[620px] space-y-2 overflow-y-auto pr-1">
            {records.map((r) => {
              const isSelected = activeRecord?.id === r.id
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRecordId(r.id)}
                  className={`cursor-pointer rounded-lg border p-3.5 text-left transition-all ${
                    isSelected
                      ? 'border-cyan-500/60 bg-cyan-950/40 shadow-md'
                      : 'border-slate-800 bg-slate-950/50 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="mb-1.5 flex items-center justify-between">
                    <span
                      className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold uppercase ${
                        r.priority === 'critical'
                          ? 'border border-rose-800 bg-rose-950 text-rose-400'
                          : r.priority === 'high'
                            ? 'border border-amber-800 bg-amber-950 text-amber-400'
                            : 'border border-blue-800 bg-blue-950 text-blue-400'
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
                  <div className="mt-2 flex items-center justify-between font-mono text-[11px] text-slate-400">
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
            <div className="space-y-5 rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
              {/* Top Overview & Verification Status */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-800 px-2.5 py-0.5 font-mono text-xs font-semibold text-slate-300 uppercase">
                      {activeRecord.maintenance_type}
                    </span>
                    <span className="font-mono text-xs text-slate-400">
                      Asset:{' '}
                      {activeRecord.equipment_asset_tag ||
                        activeRecord.equipment_name ||
                        'Electric Motor'}
                    </span>
                  </div>
                  <h3 className="mt-1.5 text-lg font-bold text-white">{activeRecord.title}</h3>
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
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md hover:bg-emerald-500"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      Verify Completion
                    </button>
                  ) : (
                    <div className="text-right">
                      <span className="flex items-center gap-1 rounded border border-emerald-800 bg-emerald-950 px-2.5 py-1 font-mono text-xs font-bold text-emerald-300">
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
              <div className="grid grid-cols-2 gap-4 rounded-lg border border-slate-800 bg-slate-950/60 p-4 font-mono text-xs">
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">
                    Work Order Status
                  </span>
                  <span className="font-semibold text-white capitalize">
                    {activeRecord.status.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">Outcome</span>
                  <span className="font-semibold text-emerald-400 capitalize">
                    {activeRecord.outcome.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">Created Date</span>
                  <span className="text-slate-300">
                    {new Date(activeRecord.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">
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
                  <h4 className="flex items-center gap-2 text-xs font-bold tracking-wider text-slate-300 uppercase">
                    <Paperclip className="h-4 w-4 text-cyan-400" />
                    Inspection Photos & PDF Documentation ({activeRecord.attachments?.length || 0})
                  </h4>
                </div>

                {/* Upload Form */}
                <form
                  onSubmit={handleFileUpload}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 text-xs"
                >
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="text-slate-400 file:mr-3 file:rounded-md file:border-0 file:bg-slate-800 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-200 hover:file:bg-slate-700"
                  />
                  <button
                    type="submit"
                    disabled={!uploadFile || isUploading}
                    className="flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3.5 py-1.5 font-semibold text-white hover:bg-cyan-500 disabled:opacity-50"
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
                        className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs"
                      >
                        <div className="flex items-center gap-2.5 truncate pr-3">
                          <FileText className="h-4 w-4 shrink-0 text-cyan-400" />
                          <div>
                            <span className="block truncate font-semibold text-slate-200">
                              {f.original_filename}
                            </span>
                            <span className="font-mono text-[10px] text-slate-500">
                              {(f.size_bytes / 1024).toFixed(1)} KB • SHA: {f.checksum.slice(0, 10)}
                              ...
                            </span>
                          </div>
                        </div>

                        <a
                          href={`/api/v1/files/${f.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1.5 rounded border border-slate-700 bg-slate-800 px-3 py-1 font-mono text-[11px] text-cyan-400 hover:bg-slate-700"
                        >
                          <Download className="h-3 w-3" />
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-800 p-4 text-center text-xs text-slate-500">
                    No files or inspection photos attached yet.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-12 text-center text-sm text-slate-400">
              Select or create a work order to review task execution and documentation.
            </div>
          )}
        </div>
      </div>

      {/* Create Work Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create Maintenance Work Order</h3>
            <form onSubmit={handleCreateWorkOrder} className="space-y-3 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-400">Work Order Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Drive-End Front Bearing Replacement"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-400">Equipment</label>
                <select
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
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
                  <label className="mb-1 block font-mono text-slate-400">Type</label>
                  <select
                    value={maintenanceType}
                    onChange={(e) => setMaintenanceType(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="corrective">Corrective</option>
                    <option value="preventive">Preventive</option>
                    <option value="condition_based">Condition Based</option>
                    <option value="emergency">Emergency</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-mono text-slate-400">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-400">Description & Tasks</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Task scope, replacement parts, and safety lockout requirements..."
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white hover:bg-cyan-500"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white">Technician / Supervisor Verification</h3>
            <form onSubmit={handleVerifySubmit} className="space-y-3 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-400">Verification Status</label>
                <select
                  value={verificationStatus}
                  onChange={(e: any) => setVerificationStatus(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="verified">Verified (Task completed and inspected)</option>
                  <option value="rejected">Rejected (Rework required)</option>
                </select>
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-400">Verification Note</label>
                <textarea
                  required
                  rows={3}
                  value={verificationNote}
                  onChange={(e) => setVerificationNote(e.target.value)}
                  placeholder="e.g. Clearance measured at 0.045mm within manufacturer specification. Unit run-tested for 30 minutes nominal."
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowVerifyModal(false)}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-500"
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
