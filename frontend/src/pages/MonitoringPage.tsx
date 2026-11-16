import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Plus, Radio, Sparkles, X, Activity } from 'lucide-react'
import { api } from '../lib/api'
import type { Equipment, MonitoringRule } from '../types/api'

export const MonitoringPage: React.FC = () => {
  const [activeScenario, setActiveScenario] = useState<string>('normal')
  const [isSimulating, setIsSimulating] = useState(false)
  const [banner, setBanner] = useState<string | null>(null)
  const [showRuleModal, setShowRuleModal] = useState(false)

  // Fetch Equipment
  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  // Fetch Rules
  const { data: rules = [], refetch: refetchRules } = useQuery({
    queryKey: ['rules'],
    queryFn: () => api.get<MonitoringRule[]>('/monitoring/rules'),
  })

  const targetMotor = equipment[0]

  // Synthetic local chart feed representing telemetry stream
  const [chartData, setChartData] = useState(() => {
    return Array.from({ length: 20 }).map((_, i) => ({
      time: `14:${20 + Math.floor(i / 2)}:${(i * 3) % 60}`,
      temperature: 52.0 + Math.sin(i) * 1.5,
      vibration: 0.12 + Math.cos(i) * 0.02,
    }))
  })

  // Rule Form state
  const [ruleName, setRuleName] = useState('')
  const [measurementType, setMeasurementType] = useState('temperature')
  const [operator, setOperator] = useState('gt')
  const [threshold, setThreshold] = useState('75.0')
  const [severity, setSeverity] = useState('high')

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/monitoring/rules', {
        name: ruleName,
        measurement_type: measurementType,
        operator,
        threshold: parseFloat(threshold),
        unit: measurementType === 'temperature' ? '°C' : 'mm/s',
        severity,
        duration_seconds: 0,
      })
      setShowRuleModal(false)
      setBanner('Monitoring rule created successfully.')
      refetchRules()
    } catch (err: any) {
      setBanner(`Rule creation failed: ${err.message}`)
    }
  }

  const handleRunSimulation = async (
    scenarioKey: 'normal' | 'overheating' | 'bearing_wear' | 'combined',
  ) => {
    if (!targetMotor) return
    setIsSimulating(true)
    setActiveScenario(scenarioKey)
    setBanner(`Running deterministic ${scenarioKey} simulation scenario...`)

    try {
      const now = Date.now()
      const baseTemp = scenarioKey === 'overheating' || scenarioKey === 'combined' ? 95.0 : 54.0
      const baseVib = scenarioKey === 'bearing_wear' || scenarioKey === 'combined' ? 1.85 : 0.14

      const newReadings = Array.from({ length: 15 }).map((_, i) => ({
        equipment_id: targetMotor.id,
        timestamp: new Date(now - (15 - i) * 1000).toISOString(),
        temperature_c: baseTemp + i * 0.4,
        vibration_value: baseVib + (i % 3) * 0.05,
        speed_rpm: 1450,
      }))

      await api.post('/readings/batch', { readings: newReadings })

      // Update local chart visualization
      setChartData((prev) => [
        ...prev.slice(10),
        ...newReadings.map((r, idx) => ({
          time: `14:35:${idx * 2}`,
          temperature: r.temperature_c,
          vibration: r.vibration_value,
        })),
      ])

      setBanner(
        `Scenario '${scenarioKey}' injected. Rules evaluated and alerts triggered if violated.`,
      )
    } catch (err: any) {
      setBanner(`Simulation failed: ${err.message}`)
    } finally {
      setIsSimulating(false)
      setTimeout(() => setBanner(null), 5000)
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
          <h2 className="text-xl font-bold tracking-tight text-white drop-shadow-sm">
            Live Telemetry & Evaluation Rules
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Real-time condition telemetry streaming, threshold rule monitoring, and fault injection
            simulator.
          </p>
        </div>

        <button
          onClick={() => setShowRuleModal(true)}
          className="glass-btn-primary flex items-center gap-1.5 px-4 py-2 text-xs font-semibold"
        >
          <Plus className="h-4 w-4" />
          Create Rule
        </button>
      </div>

      {/* Telemetry Chart */}
      <div className="glass-panel relative overflow-hidden p-6 shadow-2xl">
        <div className="absolute -top-10 -right-10 h-36 w-36 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 animate-pulse text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">
              Dual-Channel Sensor Plot (Temperature & Vibration RMS)
            </h3>
          </div>
          <span className="glass-pill glass-pill-cyan font-mono text-[11px]">
            Asset: {targetMotor?.asset_tag || 'MTR-001'}
          </span>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" stroke="#38bdf8" tick={{ fontSize: 11 }} unit="°C" />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#f43f5e"
                tick={{ fontSize: 11 }}
                unit="mm/s"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  backdropFilter: 'blur(16px)',
                  borderColor: 'rgba(255, 255, 255, 0.15)',
                  fontSize: '12px',
                  borderRadius: '12px',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="temperature"
                name="Stator Temp (°C)"
                stroke="#38bdf8"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="vibration"
                name="Drive-End Vibration (mm/s)"
                stroke="#f43f5e"
                strokeWidth={2.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scenario Ingestion Simulator Panel */}
      <div className="glass-panel p-6 shadow-xl">
        <div className="mb-2 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">
            Deterministic Fault Injection Simulator
          </h3>
        </div>
        <p className="mb-4 text-xs text-slate-400">
          Inject mathematical scenario windows into the ingestion engine to trigger threshold
          evaluation rules and alert lifecycles in real-time.
        </p>

        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-4">
          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('normal')}
            className={`glass-panel-interactive rounded-xl p-3.5 text-left transition-all ${
              activeScenario === 'normal'
                ? 'border-emerald-400/50 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                : 'border-white/5 bg-slate-950/40 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-white">Nominal Operating</span>
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div className="mt-1 text-[11px] text-slate-400">52°C Temp, 0.14 mm/s Vibration</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('overheating')}
            className={`glass-panel-interactive rounded-xl p-3.5 text-left transition-all ${
              activeScenario === 'overheating'
                ? 'border-amber-400/50 bg-amber-500/10 shadow-lg shadow-amber-500/10'
                : 'border-white/5 bg-slate-950/40 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-white">Thermal Overload</span>
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
            </div>
            <div className="mt-1 text-[11px] text-slate-400">95°C+ Temp, Rules breach</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('bearing_wear')}
            className={`glass-panel-interactive rounded-xl p-3.5 text-left transition-all ${
              activeScenario === 'bearing_wear'
                ? 'border-rose-400/50 bg-rose-500/10 shadow-lg shadow-rose-500/10'
                : 'border-white/5 bg-slate-950/40 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-white">Bearing Flaking</span>
              <span className="h-2 w-2 rounded-full bg-rose-400 animate-pulse" />
            </div>
            <div className="mt-1 text-[11px] text-slate-400">1.85 mm/s Peak, BPFO pulses</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('combined')}
            className={`glass-panel-interactive rounded-xl p-3.5 text-left transition-all ${
              activeScenario === 'combined'
                ? 'border-purple-400/50 bg-purple-500/10 shadow-lg shadow-purple-500/10'
                : 'border-white/5 bg-slate-950/40 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-white">Combined Failure</span>
              <span className="h-2 w-2 rounded-full bg-purple-400 animate-pulse" />
            </div>
            <div className="mt-1 text-[11px] text-slate-400">Concurrent heat & vibration</div>
          </button>
        </div>
      </div>

      {/* Rules Table */}
      <div className="glass-panel overflow-hidden p-6 shadow-xl">
        <h3 className="mb-4 text-sm font-semibold text-white">
          Active Monitoring Rules ({rules.length})
        </h3>
        <div className="overflow-x-auto rounded-xl border border-white/5 bg-slate-950/40">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/5 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="p-3.5">Rule Name</th>
                <th className="p-3.5">Measurement</th>
                <th className="p-3.5">Condition</th>
                <th className="p-3.5">Severity</th>
                <th className="p-3.5">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rules.map((r) => (
                <tr key={r.id} className="transition-colors hover:bg-white/[0.04]">
                  <td className="p-3.5 font-semibold text-white">{r.name}</td>
                  <td className="p-3.5 font-mono text-cyan-300 capitalize">{r.measurement_type}</td>
                  <td className="p-3.5 font-mono text-slate-200">
                    {r.operator.toUpperCase()} {r.threshold} {r.unit}
                  </td>
                  <td className="p-3.5">
                    <span
                      className={`glass-pill text-[10px] uppercase font-mono ${
                        r.severity === 'critical'
                          ? 'glass-pill-critical'
                          : 'glass-pill-warning'
                      }`}
                    >
                      {r.severity}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className="glass-pill glass-pill-emerald text-[10px]">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" /> Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Rule Modal (Apple Frosted Glass Sheet) */}
      {showRuleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md transition-all">
          <div className="glass-panel w-full max-w-md space-y-4 p-6 shadow-2xl border-white/15 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Add Monitoring Threshold Rule</h3>
              <button
                onClick={() => setShowRuleModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCreateRule} className="space-y-3.5 text-xs">
              <div>
                <label className="mb-1 block font-mono text-slate-300">Rule Name</label>
                <input
                  type="text"
                  required
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  placeholder="e.g. Bearing High Temperature Warning"
                  className="glass-input w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block font-mono text-slate-300">Measurement</label>
                  <select
                    value={measurementType}
                    onChange={(e) => setMeasurementType(e.target.value)}
                    className="glass-input w-full"
                  >
                    <option value="temperature">Temperature (°C)</option>
                    <option value="vibration">Vibration (mm/s)</option>
                    <option value="speed">Rotational Speed (RPM)</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-mono text-slate-300">Operator</label>
                  <select
                    value={operator}
                    onChange={(e) => setOperator(e.target.value)}
                    className="glass-input w-full"
                  >
                    <option value="gt">Greater Than (&gt;)</option>
                    <option value="gte">Greater or Equal (&ge;)</option>
                    <option value="lt">Less Than (&lt;)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block font-mono text-slate-300">Threshold</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="glass-input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block font-mono text-slate-300">Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="glass-input w-full"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="glass-btn px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="glass-btn-primary px-4 py-2 font-semibold text-white"
                >
                  Create Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default MonitoringPage
