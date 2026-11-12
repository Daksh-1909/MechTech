import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Network,
  Play,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  UserCheck,
  Wrench,
  XCircle,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Diagnosis, Equipment } from '../types/api'

export const DiagnosticsPage: React.FC = () => {
  const [selectedDiagId, setSelectedDiagId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [reviewModal, setReviewModal] = useState<Diagnosis | null>(null)
  const [reviewDecision, setReviewDecision] = useState<'confirmed_by_reviewer' | 'dismissed'>('confirmed_by_reviewer')
  const [reviewNote, setReviewNote] = useState('')
  const [banner, setBanner] = useState<string | null>(null)

  // Fetch Equipment
  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  // Fetch Diagnoses
  const { data: diagnoses = [], refetch, isLoading } = useQuery({
    queryKey: ['diagnoses'],
    queryFn: () => api.get<Diagnosis[]>('/diagnoses'),
  })

  const targetEquipment = equipment[0]
  const activeDiagnosis =
    diagnoses.find((d) => d.id === selectedDiagId) || diagnoses[0]

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
      setBanner(`Hybrid diagnosis completed: ${res.status.toUpperCase()} (${Math.round(res.confidence_score * 100)}% confidence).`)
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
        <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-200 text-xs font-mono flex items-center justify-between">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">✕</button>
        </div>
      )}

      {/* Header & Generate Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Hybrid Fault Diagnostics</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
              Rules + ML + Knowledge Graph
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Explainable fault isolation fusing threshold heuristics, scikit-learn models, and NetworkX ontology reasoning.
          </p>
        </div>

        <button
          disabled={isGenerating || !targetEquipment}
          onClick={handleGenerateDiagnosis}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-600/20 disabled:opacity-50 transition-all"
        >
          <Cpu className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
          {isGenerating ? 'Analyzing Telemetry Window...' : 'Run Hybrid Diagnosis'}
        </button>
      </div>

      {/* Mandatory Advisory Notice */}
      <div className="rounded-xl bg-amber-950/40 border border-amber-800/40 p-4 text-xs font-mono text-amber-200/90 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-amber-300 uppercase tracking-wider block">
            Advisory Diagnostic Output:
          </span>
          Predictions are derived from simulated feature windows and rule thresholds. Results are advisory and must be verified by a qualified technician prior to executing mechanical overhaul.
        </div>
      </div>

      {/* Main Grid: Diagnosis Selector & Detailed Multi-Layer Evidence Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Historical Diagnoses List */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">
            Diagnosis Records ({diagnoses.length})
          </h3>
          <div className="space-y-2 overflow-y-auto max-h-[600px] pr-1">
            {diagnoses.map((d) => {
              const isSelected = activeDiagnosis?.id === d.id
              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDiagId(d.id)}
                  className={`p-3.5 rounded-lg border text-left cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-950/40 border-blue-500/60 shadow-md'
                      : 'bg-slate-950/50 border-slate-800 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-semibold ${
                        d.status === 'normal'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {d.status.replace('_', ' ')}
                    </span>
                    <span className="text-[11px] font-mono text-cyan-300">
                      {Math.round(d.confidence_score * 100)}%
                    </span>
                  </div>

                  <div className="font-semibold text-white text-xs tracking-tight">
                    {d.primary_fault_name || 'Nominal Condition'}
                  </div>

                  <div className="text-[11px] text-slate-400 font-mono mt-2 flex items-center justify-between">
                    <span>{new Date(d.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span className="capitalize">{d.review_status.replace('_', ' ')}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right 2 Columns: Multi-Layer Evidence Explorer */}
        <div className="lg:col-span-2 space-y-5">
          {activeDiagnosis ? (
            <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl space-y-5">
              {/* Top Summary & Review Trigger */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-mono uppercase font-bold ${
                        activeDiagnosis.status === 'normal'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {activeDiagnosis.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Policy v{activeDiagnosis.diagnostic_policy_version}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1.5">
                    {activeDiagnosis.primary_fault_name || 'Normal Operating State'}
                  </h3>
                  <p className="text-xs text-slate-300 mt-0.5 max-w-xl">{activeDiagnosis.summary}</p>
                </div>

                {/* Review status / Action */}
                <div className="flex flex-col items-end gap-1.5">
                  {activeDiagnosis.review_status === 'pending' ? (
                    <button
                      onClick={() => setReviewModal(activeDiagnosis)}
                      className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      Record Human Review
                    </button>
                  ) : (
                    <div className="text-right">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 inline-block font-semibold">
                        {activeDiagnosis.review_status.replace('_', ' ')}
                      </span>
                      {activeDiagnosis.review_note && (
                        <div className="text-[11px] text-slate-400 font-mono mt-1 max-w-xs truncate">
                          "{activeDiagnosis.review_note}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Layer 1: Rule Evidence */}
              <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Layer 1: Rule Violations & Symptoms
                    </h4>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">Weight: 1.0</span>
                </div>
                {ruleEvidence ? (
                  <div className="text-xs font-mono space-y-1.5 pt-1">
                    <div className="text-slate-300">
                      Violations Count:{' '}
                      <span className="text-white font-bold">
                        {ruleEvidence.details_json.violations?.length || 0}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {ruleEvidence.details_json.symptoms?.map((sym: string) => (
                        <span
                          key={sym}
                          className="px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800 text-[10px]"
                        >
                          {sym}
                        </span>
                      ))}
                      {(!ruleEvidence.details_json.symptoms ||
                        ruleEvidence.details_json.symptoms.length === 0) && (
                        <span className="text-emerald-400 text-xs">
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
              <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Layer 2: Scikit-learn Classifier Prediction
                    </h4>
                  </div>
                  <span className="text-[11px] font-mono text-cyan-300">
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
                          mlEvidence.details_json.is_uncertain ? 'text-amber-400' : 'text-emerald-400'
                        }
                      >
                        {mlEvidence.details_json.is_uncertain ? 'Uncertain (Flagged)' : 'Calibrated'}
                      </span>
                    </div>

                    {/* Probabilities distribution */}
                    {mlEvidence.details_json.probabilities && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] font-mono uppercase text-slate-400 block">
                          Class Probabilities Distribution:
                        </span>
                        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                          {Object.entries(mlEvidence.details_json.probabilities).map(
                            ([cls, prob]: [string, any]) => (
                              <div
                                key={cls}
                                className="p-2 rounded bg-slate-900 border border-slate-800 flex items-center justify-between"
                              >
                                <span className="capitalize text-slate-300">{cls.replace('_', ' ')}</span>
                                <span className="font-bold text-cyan-300">
                                  {Math.round(prob * 100)}%
                                </span>
                              </div>
                            )
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
              <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Layer 3: NetworkX Knowledge Graph Traversal & Remediation
                    </h4>
                  </div>
                  <span className="text-[11px] font-mono text-purple-300">Ontology Engine</span>
                </div>
                {graphEvidence ? (
                  <div className="space-y-3 pt-1 text-xs">
                    {/* Affected Components */}
                    {graphEvidence.details_json.affected_components?.length > 0 && (
                      <div>
                        <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                          Impaired Component (AFFECTS):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {graphEvidence.details_json.affected_components.map((c: any) => (
                            <span
                              key={c.key}
                              className="px-2 py-1 rounded bg-slate-900 text-slate-200 border border-slate-700 font-mono"
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
                        <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                          Recommended Physical Inspection (CHECK_WITH):
                        </span>
                        <div className="space-y-1">
                          {graphEvidence.details_json.diagnostic_procedures.map((p: any) => (
                            <div
                              key={p.key}
                              className="p-2 rounded bg-slate-900/90 border border-blue-900/40 text-blue-200 flex items-center gap-2"
                            >
                              <Wrench className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                              <span>{p.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Repair Actions */}
                    {graphEvidence.details_json.repair_actions?.length > 0 && (
                      <div>
                        <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                          Remediation Plan (MAY_BE_RESOLVED_BY):
                        </span>
                        <div className="space-y-1">
                          {graphEvidence.details_json.repair_actions.map((r: any) => (
                            <div
                              key={r.key}
                              className="p-2 rounded bg-slate-900/90 border border-emerald-900/40 text-emerald-200 flex items-center gap-2"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                              <span>{r.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">No knowledge graph traversal evidence recorded.</div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
              Select or generate a diagnosis to view the multi-layer explainable evidence.
            </div>
          )}
        </div>
      </div>

      {/* Human Review Modal */}
      {reviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Record Human Review & Decision</h3>
            <p className="text-xs text-slate-400">
              Review advisory fault prediction for{' '}
              <span className="text-white font-semibold">
                {reviewModal.primary_fault_name || 'Diagnostic Record'}
              </span>
              .
            </p>
            <form onSubmit={handleReviewSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Review Decision</label>
                <select
                  value={reviewDecision}
                  onChange={(e: any) => setReviewDecision(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="confirmed_by_reviewer">Confirm Diagnosis (Physical inspection verified)</option>
                  <option value="dismissed">Dismiss Diagnosis (Transient false positive)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-mono mb-1">Inspection Notes & Findings</label>
                <textarea
                  required
                  rows={3}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="e.g. Visual grease inspection confirmed flaking in drive-end bearing race."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReviewModal(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold"
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

