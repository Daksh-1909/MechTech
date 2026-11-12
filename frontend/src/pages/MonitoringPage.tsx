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
import {
  Activity,
  AlertTriangle,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Sparkles,
  Sliders,
} from 'lucide-react'
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

  const handleRunSimulation = async (scenarioKey: 'normal' | 'overheating' | 'bearing_wear' | 'combined') => {
    if (!targetMotor) return
    setIsSimulating(true)
    setActiveScenario(scenarioKey)
    setBanner(`Running deterministic ${scenarioKey} simulation scenario...`)

    try {
      const now = Date.now()
      const baseTemp =
        scenarioKey === 'overheating' || scenarioKey === 'combined' ? 95.0 : 54.0
      const baseVib =
        scenarioKey === 'bearing_wear' || scenarioKey === 'combined' ? 1.85 : 0.14

      const newReadings = Array.from({ length: 15 }).map((_, i) => ({
        equipment_id: targetMotor.id,
        timestamp: new Date(now - (15 - i) * 1000).toISOString(),
        temperature_c: baseTemp + (i * 0.4),
        vibration_value: baseVib + ((i % 3) * 0.05),
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

      setBanner(`Scenario '${scenarioKey}' injected. Rules evaluated and alerts triggered if violated.`)
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
        <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-200 text-xs font-mono flex items-center justify-between">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="text-cyan-400">✕</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Live Telemetry & Evaluation Rules</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time condition telemetry streaming, threshold rule monitoring, and fault injection simulator.
          </p>
        </div>

        <button
          onClick={() => setShowRuleModal(true)}
          className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-cyan-600/20"
        >
          <Plus className="w-4 h-4" />
          Create Rule
        </button>
      </div>

      {/* Telemetry Chart */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            <h3 className="text-sm font-semibold text-white">
              Dual-Channel Sensor Plot (Temperature & Vibration RMS)
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Asset: {targetMotor?.asset_tag || 'MTR-001'}</span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" stroke="#38bdf8" tick={{ fontSize: 11 }} unit="°C" />
              <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" tick={{ fontSize: 11 }} unit="mm/s" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  fontSize: '12px',
                  borderRadius: '8px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="temperature"
                name="Stator Temp (°C)"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="vibration"
                name="Drive-End Vibration (mm/s)"
                stroke="#f43f5e"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scenario Ingestion Simulator Panel */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">Deterministic Fault Injection Simulator</h3>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Inject mathematical scenario windows into the ingestion engine to trigger threshold evaluation rules and alert lifecycles in real-time.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('normal')}
            className={`p-3 rounded-lg border text-left transition-all ${
              activeScenario === 'normal'
                ? 'bg-emerald-950/60 border-emerald-500/60 text-emerald-200'
                : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="font-semibold text-xs flex items-center justify-between">
              <span>Nominal Operating</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">52°C Temp, 0.14 mm/s Vibration</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('overheating')}
            className={`p-3 rounded-lg border text-left transition-all ${
              activeScenario === 'overheating'
                ? 'bg-amber-950/60 border-amber-500/60 text-amber-200'
                : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="font-semibold text-xs flex items-center justify-between">
              <span>Thermal Overload</span>
              <span className="w-2 h-2 rounded-full bg-amber-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">95°C+ Temp, Rules breach</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('bearing_wear')}
            className={`p-3 rounded-lg border text-left transition-all ${
              activeScenario === 'bearing_wear'
                ? 'bg-rose-950/60 border-rose-500/60 text-rose-200'
                : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="font-semibold text-xs flex items-center justify-between">
              <span>Bearing Flaking</span>
              <span className="w-2 h-2 rounded-full bg-rose-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">1.85 mm/s Peak, BPFO pulses</div>
          </button>

          <button
            disabled={isSimulating}
            onClick={() => handleRunSimulation('combined')}
            className={`p-3 rounded-lg border text-left transition-all ${
              activeScenario === 'combined'
                ? 'bg-purple-950/60 border-purple-500/60 text-purple-200'
                : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <div className="font-semibold text-xs flex items-center justify-between">
              <span>Combined Failure</span>
              <span className="w-2 h-2 rounded-full bg-purple-400" />
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Concurrent heat & vibration</div>
          </button>
        </div>
      </div>

      {/* Rules Table */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
        <h3 className="text-sm font-semibold text-white mb-3">Active Monitoring Rules ({rules.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-mono uppercase text-[10px]">
              <tr>
                <th className="p-3">Rule Name</th>
                <th className="p-3">Measurement</th>
                <th className="p-3">Condition</th>
                <th className="p-3">Severity</th>
                <th className="p-3">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40">
                  <td className="p-3 font-semibold text-white">{r.name}</td>
                  <td className="p-3 font-mono text-cyan-300 capitalize">{r.measurement_type}</td>
                  <td className="p-3 font-mono text-slate-200">
                    {r.operator.toUpperCase()} {r.threshold} {r.unit}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                        r.severity === 'critical'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {r.severity}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Rule Modal */}
      {showRuleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Add Monitoring Threshold Rule</h3>
            <form onSubmit={handleCreateRule} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  placeholder="e.g. Bearing High Temperature Warning"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Measurement</label>
                  <select
                    value={measurementType}
                    onChange={(e) => setMeasurementType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="temperature">Temperature (°C)</option>
                    <option value="vibration">Vibration (mm/s)</option>
                    <option value="speed">Rotational Speed (RPM)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Operator</label>
                  <select
                    value={operator}
                    onChange={(e) => setOperator(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="gt">Greater Than (&gt;)</option>
                    <option value="gte">Greater or Equal (&ge;)</option>
                    <option value="lt">Less Than (&lt;)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Threshold</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold"
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

