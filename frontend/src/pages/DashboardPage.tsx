import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Play,
  RotateCcw,
  Sparkles,
  Wrench,
  Radio,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Alert, Diagnosis, Equipment, EquipmentHealthStatus } from '../types/api'
import MotorScene from '../components/motor3d/MotorScene'

export const DashboardPage: React.FC = () => {
  const [exploded3D, setExploded3D] = useState(false)
  const [isRotating, setIsRotating] = useState(true)
  const [selectedComp, setSelectedComp] = useState<string | null>('bearing_front')
  const [simulating, setSimulating] = useState(false)
  const [simMessage, setSimMessage] = useState<string | null>(null)

  // Fetch Equipment
  const { data: equipmentList = [] } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  // Fetch Alerts
  const { data: alerts = [], refetch: refetchAlerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.get<Alert[]>('/alerts?limit=10'),
  })

  // Fetch Diagnoses
  const { data: diagnoses = [], refetch: refetchDiagnoses } = useQuery({
    queryKey: ['diagnoses'],
    queryFn: () => api.get<Diagnosis[]>('/diagnoses?limit=5'),
  })

  // Primary demo motor
  const demoMotor = equipmentList[0]

  // Status computation
  const openAlerts = alerts.filter((a) => a.status === 'open' || a.status === 'acknowledged')
  const criticalAlerts = openAlerts.filter((a) => a.severity === 'critical')
  const latestDiagnosis = diagnoses[0]

  // Trigger quick fault simulation from dashboard
  const handleTriggerScenario = async (scenario: 'overheating' | 'bearing_wear' | 'normal') => {
    if (!demoMotor) return
    setSimulating(true)
    setSimMessage(`Generating simulated ${scenario} scenario telemetry...`)
    try {
      // Ingest synthetic window
      const baseTemp = scenario === 'overheating' ? 92.5 : 55.0
      const baseVib = scenario === 'bearing_wear' ? 1.85 : 0.14

      const readings = Array.from({ length: 15 }).map((_, i) => ({
        equipment_id: demoMotor.id,
        timestamp: new Date(Date.now() - (15 - i) * 1000).toISOString(),
        temperature_c: baseTemp + Math.sin(i) * 0.5,
        vibration_value: baseVib + (i % 2) * 0.02,
        speed_rpm: 1450,
      }))

      await api.post('/readings/batch', { readings })
      await refetchAlerts()
      await refetchDiagnoses()
      setSimMessage(`Injected 15 readings for ${scenario} scenario successfully.`)
    } catch (err: any) {
      setSimMessage(`Simulation failed: ${err.message}`)
    } finally {
      setSimulating(false)
      setTimeout(() => setSimMessage(null), 4000)
    }
  }

  return (
    <div className="space-y-6">
      {/* Simulation Banner Notification */}
      {simMessage && (
        <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-200 text-xs font-mono flex items-center justify-between animate-in fade-in">
          <span>{simMessage}</span>
          <button onClick={() => setSimMessage(null)} className="text-cyan-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Monitored Assets</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-white">{equipmentList.length || 1}</div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" />
            100% telemetry online
          </div>
        </div>

        {/* Metric 2 */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Open Alerts</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-white">{openAlerts.length}</div>
          <div className="text-xs text-rose-400 mt-2 font-mono flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            {criticalAlerts.length} critical requiring triage
          </div>
        </div>

        {/* Metric 3 */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Diagnostic Confidence</span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-white">
            {latestDiagnosis ? `${Math.round(latestDiagnosis.confidence_score * 100)}%` : '92%'}
          </div>
          <div className="text-xs text-cyan-300 mt-2 font-mono">
            Hybrid policy v1.0 (Rule+ML+Graph)
          </div>
        </div>

        {/* Metric 4 */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Fleet Status</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-emerald-400">
            {criticalAlerts.length > 0 ? 'Attention' : 'Operational'}
          </div>
          <div className="text-xs text-slate-400 mt-2 font-mono">
            ABB M3AA 132 Induction Motor
          </div>
        </div>
      </div>

      {/* Main Grid: 3D Visualization + Live Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 3D Motor Visualization */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900/90 border border-slate-800 p-5 flex flex-col shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <span>Interactive 3D Motor Digital Twin</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  {demoMotor?.name || 'Three-Phase Induction Motor'}
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Component health state is updated continuously. Click components to isolate inspection areas.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsRotating(!isRotating)}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-mono border transition-colors ${
                  isRotating
                    ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/40'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {isRotating ? 'Pause Spin' : 'Resume Spin'}
              </button>

              <button
                onClick={() => setExploded3D(!exploded3D)}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-mono border transition-colors ${
                  exploded3D
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500'
                    : 'bg-slate-800 text-slate-300 border-slate-700 hover:text-white'
                }`}
              >
                {exploded3D ? 'Collapse View' : 'Exploded Cutaway'}
              </button>
            </div>
          </div>

          {/* 3D Canvas */}
          <MotorScene
            selectedComponentKey={selectedComp}
            onSelectComponent={(key) => setSelectedComp(key)}
            exploded={exploded3D}
            isRunning={isRotating}
            componentStatuses={{
              bearing_front: {
                key: 'bearing_front',
                name: 'Drive-End Front Bearing',
                status: criticalAlerts.length > 0 ? 'critical' : 'normal',
                metricLabel: 'Peak Vibration',
                metricValue: criticalAlerts.length > 0 ? '1.85 mm/s (ALERT)' : '0.14 mm/s',
              },
              stator: {
                key: 'stator',
                name: 'Copper Stator Windings',
                status: 'normal',
                metricLabel: 'Winding Temp',
                metricValue: '58.4 °C',
              },
              cooling_fan: {
                key: 'cooling_fan',
                name: 'Bi-directional Cooling Fan',
                status: 'normal',
                metricLabel: 'Airflow Speed',
                metricValue: '1450 RPM',
              },
            }}
          />

          {/* Quick Scenario Simulator Ingestion Toolbar */}
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="text-slate-400 font-mono flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Simulate Scenario:</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('normal')}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-mono disabled:opacity-50"
              >
                Nominal State
              </button>
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('overheating')}
                className="px-2.5 py-1 rounded bg-amber-950/60 hover:bg-amber-900 text-amber-200 border border-amber-800/60 font-mono disabled:opacity-50"
              >
                Stator Overheating
              </button>
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('bearing_wear')}
                className="px-2.5 py-1 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-200 border border-rose-800/60 font-mono disabled:opacity-50"
              >
                Bearing Flaking
              </button>
            </div>
          </div>
        </div>

        {/* Right Col: Recent Diagnoses & Quick Actions */}
        <div className="space-y-6 flex flex-col justify-between">
          {/* Recent Diagnosis Card */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                Latest Hybrid Diagnosis
              </h3>
              <Link to="/diagnostics" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {latestDiagnosis ? (
              <div className="space-y-3 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold uppercase ${
                        latestDiagnosis.status === 'normal'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {latestDiagnosis.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Conf: {Math.round(latestDiagnosis.confidence_score * 100)}%
                    </span>
                  </div>
                  <h4 className="text-base font-medium text-slate-100 mt-2">
                    {latestDiagnosis.primary_fault_name || 'Nominal Operation'}
                  </h4>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    {latestDiagnosis.summary}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/80">
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                    Multi-Layer Evidence:
                  </div>
                  <div className="flex gap-2">
                    {latestDiagnosis.evidence_items?.map((ev) => (
                      <span
                        key={ev.id}
                        className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 capitalize"
                      >
                        {ev.evidence_type}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-400">
                No recent diagnoses recorded yet. Run a hybrid analysis from the Diagnostics tab.
              </div>
            )}
          </div>

          {/* Quick Action Navigation */}
          <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">Quick Navigation</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <Link
                to="/monitoring"
                className="p-3 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-200 flex flex-col gap-1 transition-colors"
              >
                <Radio className="w-4 h-4 text-cyan-400" />
                <span className="font-semibold">Sensor Plots</span>
                <span className="text-[10px] text-slate-400">Live telemetry stream</span>
              </Link>
              <Link
                to="/maintenance"
                className="p-3 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-200 flex flex-col gap-1 transition-colors"
              >
                <Wrench className="w-4 h-4 text-amber-400" />
                <span className="font-semibold">Work Orders</span>
                <span className="text-[10px] text-slate-400">Inspect & verify repairs</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage

