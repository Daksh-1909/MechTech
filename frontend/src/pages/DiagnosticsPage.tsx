import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  UserCheck,
  Wrench,
  X,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Diagnosis, Equipment } from '../types/api'

export const DiagnosticsPage: React.FC = () => {
  const [selectedDiagId, setSelectedDiagId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [reviewModal, setReviewModal] = useState<Diagnosis | null>(null)
  const [reviewDecision, setReviewDecision] = useState<'confirmed_by_reviewer' | 'dismissed'>(
    'confirmed_by_reviewer',
  )
  const [reviewNote, setReviewNote] = useState('')
  const [banner, setBanner] = useState<string | null>(null)

  // Fetch Equipment
  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  // Fetch Diagnoses
  const { data: diagnoses = [], refetch } = useQuery({
    queryKey: ['diagnoses'],
    queryFn: () => api.get<Diagnosis[]>('/diagnoses'),
  })

  const targetEquipment = equipment[0]
  const activeDiagnosis = diagnoses.find((d) => d.id === selectedDiagId) || diagnoses[0]

  const handleGenerateDiagnosis = async () => {
    if (!targetEquipment) return
    setIsGenerating(true)
    setBanner('Orchestrating Rules + ML + Knowledge Graph analysis...')
    try {
      const res = await api.post<Diagnosis>('/diagnoses/generate', {
        equipment_id: targetEquipment.id,
        window_size: 15,
      })
      await refetch()
      setSelectedDiagId(res.id)
      setBanner(
        `Hybrid diagnosis completed: ${res.status.toUpperCase()} (${Math.round(res.confidence_score * 100)}% confidence).`,
      )
    } catch (err: any) {
      setBanner(`Diagnostic generation failed: ${err.message}`)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reviewModal) return
    try {
      await api.post(`/diagnoses/${reviewModal.id}/review`, {
        review_status: reviewDecision,
        review_note: reviewNote || 'Verified during physical inspection.',
      })
      setReviewModal(null)
      setReviewNote('')
      setBanner('Diagnosis review recorded and audited.')
      refetch()
    } catch (err: any) {
      setBanner(`Review failed: ${err.message}`)
    }
  }

  // Parse evidence types
  const ruleEvidence = activeDiagnosis?.evidence_items?.find((e) => e.evidence_type === 'rule')
  const mlEvidence = activeDiagnosis?.evidence_items?.find((e) => e.evidence_type === 'prediction')
  const graphEvidence = activeDiagnosis?.evidence_items?.find((e) => e.evidence_type === 'graph')

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

      {/* Header & Generate Button */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="flex items-center gap-2.5 text-xl font-bold tracking-tight text-white drop-shadow-sm">
            <span>Hybrid Fault Diagnostics</span>
            <span className="glass-pill glass-pill-cyan font-mono text-xs font-semibold">
              Rules + ML + Knowledge Graph
            </span>
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Explainable fault isolation fusing threshold heuristics, scikit-learn models, and
            NetworkX ontology reasoning.
          </p>
        </div>

        <button
          disabled={isGenerating || !targetEquipment}
          onClick={handleGenerateDiagnosis}
          className="glass-btn-primary flex items-center gap-2 px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50"
        >
          <Cpu className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
          {isGenerating ? 'Analyzing Telemetry Window...' : 'Run Hybrid Diagnosis'}
        </button>
      </div>

      {/* Mandatory Advisory Notice */}
      <div className="glass-panel relative overflow-hidden flex items-start gap-3.5 border-amber-500/30 bg-amber-950/20 p-4 font-mono text-xs text-amber-200/95">
        <div className="absolute top-0 right-0 h-24 w-24 rounded-full bg-amber-500/10 blur-xl pointer-events-none" />
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
        <div>
          <span className="block font-bold tracking-wider text-amber-300 uppercase">
            Advisory Diagnostic Notice (ISO 13374 / Condition Monitoring):
          </span>
          Predictions are derived from simulated feature windows and heuristic rule thresholds.
          Results are purely advisory and must be verified by a qualified technician prior to
          executing physical mechanical overhaul or machine shutdown.
        </div>
      </div>

      {/* Main Grid: Diagnosis Selector & Detailed Multi-Layer Evidence Explorer */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Historical Diagnoses List */}
        <div className="glass-panel p-5 shadow-xl">
          <h3 className="mb-3.5 font-mono text-xs tracking-wider text-slate-400 uppercase">
            Diagnosis Records ({diagnoses.length})
          </h3>
          <div className="max-h-[620px] space-y-2.5 overflow-y-auto pr-1">
            {diagnoses.map((d) => {
              const isSelected = activeDiagnosis?.id === d.id
              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDiagId(d.id)}
                  className={`glass-panel-interactive cursor-pointer rounded-xl p-3.5 text-left transition-all ${
                    isSelected
                      ? 'border-cyan-400/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10'
                      : 'border-white/5 bg-slate-950/40'
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span
                      className={`glass-pill text-[10px] uppercase font-mono ${
                        d.status === 'normal'
                          ? 'glass-pill-emerald'
                          : 'glass-pill-critical'
                      }`}
                    >
                      {d.status.replace('_', ' ')}
                    </span>
                    <span className="glass-pill glass-pill-cyan font-mono text-[11px]">
                      {Math.round(d.confidence_score * 100)}%
                    </span>
                  </div>

                  <div className="text-xs font-semibold tracking-tight text-white">
                    {d.primary_fault_name || 'Nominal Condition'}
                  </div>

                  <div className="mt-2.5 flex items-center justify-between font-mono text-[11px] text-slate-400">
                    <span>
                      {new Date(d.generated_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="capitalize">{d.review_status.replace('_', ' ')}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right 2 Columns: Multi-Layer Evidence Explorer */}
        <div className="space-y-5 lg:col-span-2">
          {activeDiagnosis ? (
            <div className="glass-panel space-y-5 p-6 shadow-2xl">
              {/* Top Summary & Review Trigger */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`glass-pill text-xs font-mono font-bold uppercase ${
                        activeDiagnosis.status === 'normal'
                          ? 'glass-pill-emerald'
                          : 'glass-pill-critical'
                      }`}
                    >
                      {activeDiagnosis.status.replace('_', ' ')}
                    </span>
                    <span className="font-mono text-xs text-slate-400">
                      Policy v{activeDiagnosis.diagnostic_policy_version}
                    </span>
                  </div>
                  <h3 className="mt-2 text-lg font-bold text-white">
                    {activeDiagnosis.primary_fault_name || 'Normal Operating State'}
                  </h3>
                  <p className="mt-1 max-w-xl text-xs text-slate-300">
                    {activeDiagnosis.summary}
                  </p>
                </div>

                {/* Review status / Action */}
                <div className="flex flex-col items-end gap-1.5">
                  {activeDiagnosis.review_status === 'pending' ? (
                    <button
                      onClick={() => setReviewModal(activeDiagnosis)}
                      className="glass-btn-primary flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      Record Human Review
                    </button>
                  ) : (
                    <div className="text-right">
                      <span className="glass-pill glass-pill-emerald font-mono text-xs font-semibold">
                        {activeDiagnosis.review_status.replace('_', ' ')}
                      </span>
                      {activeDiagnosis.review_note && (
                        <div className="mt-1 max-w-xs truncate font-mono text-[11px] text-slate-400">
                          "{activeDiagnosis.review_note}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Layer 1: Rule Evidence */}
              <div className="glass-panel-interactive space-y-2 rounded-xl p-4 border-white/5 bg-slate-950/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                    <h4 className="text-xs font-bold tracking-wider text-slate-200 uppercase">
                      Layer 1: Rule Violations & Symptoms
                    </h4>
                  </div>
                  <span className="glass-pill font-mono text-[11px] text-slate-400">Weight: 1.0</span>
                </div>
                {ruleEvidence ? (
                  <div className="space-y-2 pt-1 font-mono text-xs">
                    <div className="text-slate-300">
                      Violations Count:{' '}
                      <span className="font-bold text-white">
                        {ruleEvidence.details_json.violations?.length || 0}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {ruleEvidence.details_json.symptoms?.map((sym: string) => (
                        <span
                          key={sym}
                          className="glass-pill glass-pill-critical text-[10px]"
                        >
                          {sym}
                        </span>
                      ))}
                      {(!ruleEvidence.details_json.symptoms ||
                        ruleEvidence.details_json.symptoms.length === 0) && (
                        <span className="glass-pill glass-pill-emerald text-xs">
                          All threshold rules evaluated nominal (no symptoms).
                        </span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">No rule evidence recorded.</div>
                )}
              </div>

              {/* Layer 2: ML Model Prediction */}
              <div className="glass-panel-interactive space-y-2 rounded-xl p-4 border-white/5 bg-slate-950/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                    <h4 className="text-xs font-bold tracking-wider text-slate-200 uppercase">
                      Layer 2: Scikit-learn Classifier Prediction
                    </h4>
                  </div>
                  <span className="glass-pill glass-pill-cyan font-mono text-[11px]">
                    Model: {mlEvidence?.details_json?.model_version || '1.0.0'}
                  </span>
                </div>
                {mlEvidence ? (
                  <div className="space-y-3 pt-1 text-xs">
                    <div className="flex items-center gap-3 font-mono">
                      <span className="text-slate-400">Predicted Class:</span>
                      <span className="font-bold text-white capitalize">
                        {mlEvidence.details_json.predicted_class}
                      </span>
                      <span className="text-slate-500">|</span>
                      <span className="text-slate-400">Uncertainty:</span>
                      <span
                        className={
                          mlEvidence.details_json.is_uncertain
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                        }
                      >
                        {mlEvidence.details_json.is_uncertain
                          ? 'Uncertain (Flagged)'
                          : 'Calibrated'}
                      </span>
                    </div>

                    {/* Probabilities distribution */}
                    {mlEvidence.details_json.probabilities && (
                      <div className="space-y-1.5 pt-1">
                        <span className="block font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                          Class Probabilities Distribution:
                        </span>
                        <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                          {Object.entries(mlEvidence.details_json.probabilities).map(
                            ([cls, prob]: [string, any]) => (
                              <div
                                key={cls}
                                className="glass-panel flex items-center justify-between p-2.5 rounded-lg border-white/5 bg-slate-950/50"
                              >
                                <span className="text-slate-300 capitalize">
                                  {cls.replace('_', ' ')}
                                </span>
                                <span className="font-bold text-cyan-300">
                                  {Math.round(prob * 100)}%
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">No ML prediction evidence recorded.</div>
                )}
              </div>

              {/* Layer 3: Knowledge Graph Reasoning */}
              <div className="glass-panel-interactive space-y-2 rounded-xl p-4 border-white/5 bg-slate-950/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-purple-400 animate-pulse" />
                    <h4 className="text-xs font-bold tracking-wider text-slate-200 uppercase">
                      Layer 3: NetworkX Knowledge Graph Traversal & Remediation
                    </h4>
                  </div>
                  <span className="glass-pill font-mono text-[11px] text-purple-300">
                    Ontology Engine
                  </span>
                </div>
                {graphEvidence ? (
                  <div className="space-y-3 pt-1 text-xs">
                    {/* Affected Components */}
                    {graphEvidence.details_json.affected_components?.length > 0 && (
                      <div>
                        <span className="mb-1.5 block font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                          Impaired Component (AFFECTS):
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {graphEvidence.details_json.affected_components.map((c: any) => (
                            <span
                              key={c.key}
                              className="glass-pill glass-pill-cyan font-mono text-xs"
                            >
                              {c.label}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Diagnostic Procedures */}
                    {graphEvidence.details_json.diagnostic_procedures?.length > 0 && (
                      <div>
                        <span className="mb-1.5 block font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                          Recommended Physical Inspection (CHECK_WITH):
                        </span>
                        <div className="space-y-1.5">
                          {graphEvidence.details_json.diagnostic_procedures.map((p: any) => (
                            <div
                              key={p.key}
                              className="glass-panel flex items-center gap-2.5 p-2.5 text-blue-200 border-blue-500/20 bg-blue-950/20"
                            >
                              <Wrench className="h-3.5 w-3.5 shrink-0 text-cyan-400" />
                              <span>{p.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Repair Actions */}
                    {graphEvidence.details_json.repair_actions?.length > 0 && (
                      <div>
                        <span className="mb-1.5 block font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                          Remediation Plan (MAY_BE_RESOLVED_BY):
                        </span>
                        <div className="space-y-1.5">
                          {graphEvidence.details_json.repair_actions.map((r: any) => (
                            <div
                              key={r.key}
                              className="glass-panel flex items-center gap-2.5 p-2.5 text-emerald-200 border-emerald-500/20 bg-emerald-950/20"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
                              <span>{r.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">
                    No knowledge graph traversal evidence recorded.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-panel p-16 text-center text-sm text-slate-400">
              Select or generate a diagnosis to view the multi-layer explainable evidence.
            </div>
          )}
        </div>
      </div>

      {/* Human Review Modal (Apple Frosted Glass Sheet) */}
      {reviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md space-y-4 p-6 shadow-2xl border-white/15 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Record Human Review & Decision</h3>
              <button
                onClick={() => setReviewModal(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Review advisory fault prediction for{' '}
              <span className="font-semibold text-white">
                {reviewModal.primary_fault_name || 'Diagnostic Record'}
              </span>
              .
            </p>
            <form onSubmit={handleReviewSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-300">Review Decision</label>
                <select
                  value={reviewDecision}
                  onChange={(e: any) => setReviewDecision(e.target.value)}
                  className="glass-input w-full"
                >
                  <option value="confirmed_by_reviewer">
                    Confirm Diagnosis (Physical inspection verified)
                  </option>
                  <option value="dismissed">Dismiss Diagnosis (Transient false positive)</option>
                </select>
              </div>

              <div>
                <label className="mb-1 block font-mono text-slate-300">
                  Inspection Notes & Findings
                </label>
                <textarea
                  required
                  rows={3}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="e.g. Visual grease inspection confirmed flaking in drive-end bearing race."
                  className="glass-input w-full"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setReviewModal(null)}
                  className="glass-btn px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="glass-btn-primary px-4 py-2 font-semibold text-white"
                >
                  Save Review Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default DiagnosticsPage
