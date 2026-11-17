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
  Sparkles,
  Wrench,
  Radio,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Alert, Diagnosis, Equipment } from '../types/api'
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

  const demoMotor = equipmentList[0]
  const openAlerts = alerts.filter((a) => a.status === 'open' || a.status === 'acknowledged')
  const criticalAlerts = openAlerts.filter((a) => a.severity === 'critical')
  const latestDiagnosis = diagnoses[0]

  const handleTriggerScenario = async (scenario: 'overheating' | 'bearing_wear' | 'normal') => {
    if (!demoMotor) return
    setSimulating(true)
    setSimMessage(`Injecting synthetic ${scenario} scenario feature window...`)
    try {
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
        <div className="p-3.5 rounded-xl glass-panel border border-cyan-400/40 text-cyan-200 text-xs font-mono flex items-center justify-between shadow-[0_0_24px_rgba(6,182,212,0.25)] animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" />
            <span>{simMessage}</span>
          </div>
          <button onClick={() => setSimMessage(null)} className="text-cyan-400 hover:text-white px-2">✕</button>
        </div>
      )}

      {/* Top Liquid Glass Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="p-5 glass-panel-interactive relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-28 h-28 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-all duration-300 pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">Monitored Assets</span>
            <div className="p-2 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-400/30">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{equipmentList.length || 1}</div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1.5 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>100% online telemetry</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="p-5 glass-panel-interactive relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-28 h-28 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/20 transition-all duration-300 pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">Active Alerts</span>
            <div className="p-2 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-400/30">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{openAlerts.length}</div>
          <div className="text-xs text-rose-400 mt-2 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]" />
            <span>{criticalAlerts.length} critical requiring triage</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="p-5 glass-panel-interactive relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-28 h-28 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all duration-300 pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">Diagnostic Confidence</span>
            <div className="p-2 rounded-xl bg-blue-500/15 text-blue-400 border border-blue-400/30">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">
            {latestDiagnosis ? `${Math.round(latestDiagnosis.confidence_score * 100)}%` : '92%'}
          </div>
          <div className="text-xs text-cyan-300 mt-2 font-mono">
            Hybrid policy v1.0 (Rule+ML+Graph)
          </div>
        </div>

        {/* Metric 4 */}
        <div className="p-5 glass-panel-interactive relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all duration-300 pointer-events-none" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">Fleet Health</span>
            <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-400/30">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">
            {criticalAlerts.length > 0 ? 'Attention' : 'Operational'}
          </div>
          <div className="text-xs text-slate-400 mt-2 font-mono">
            ABB M3AA 132 Motor
          </div>
        </div>
      </div>

      {/* Main Grid: 3D Visualization + Live Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 3D Motor Visualization */}
        <div className="lg:col-span-2 glass-panel p-5 flex flex-col shadow-2xl relative">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <span>Interactive 3D Motor Digital Twin</span>
                <span className="glass-pill glass-pill-info">
                  {demoMotor?.name || 'Three-Phase Induction Motor'}
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Thermal & vibration state refreshed in real-time. Click components to isolate inspection zones.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsRotating(!isRotating)}
                className={`glass-btn text-xs font-mono ${
                  isRotating ? 'text-cyan-300 border-cyan-400/40 bg-cyan-500/10' : 'text-slate-400'
                }`}
              >
                {isRotating ? 'Pause Spin' : 'Resume Spin'}
              </button>

              <button
                onClick={() => setExploded3D(!exploded3D)}
                className={`glass-btn text-xs font-mono ${
                  exploded3D ? 'text-cyan-300 border-cyan-400/40 bg-cyan-500/20' : 'text-slate-300'
                }`}
              >
                {exploded3D ? 'Collapse View' : 'Exploded Cutaway'}
              </button>
            </div>
          </div>

          {/* 3D Canvas Viewport */}
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
          <div className="mt-4 pt-3 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="text-slate-300 font-mono flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span>Fault Injection Simulator:</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('normal')}
                className="glass-btn hover:text-white"
              >
                Nominal State
              </button>
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('overheating')}
                className="glass-btn hover:text-amber-300 hover:border-amber-400/40"
              >
                Stator Overheat
              </button>
              <button
                disabled={simulating}
                onClick={() => handleTriggerScenario('bearing_wear')}
                className="glass-btn hover:text-rose-300 hover:border-rose-400/40"
              >
                Bearing Flaking
              </button>
            </div>
          </div>
        </div>

        {/* Right Col: Recent Diagnoses & Quick Actions */}
        <div className="space-y-6 flex flex-col justify-between">
          {/* Recent Diagnosis Card */}
          <div className="glass-panel p-5 shadow-2xl flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-3 border-b border-white/[0.08]">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                Latest Hybrid Diagnosis
              </h3>
              <Link to="/diagnostics" className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {latestDiagnosis ? (
              <div className="space-y-3.5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`glass-pill ${
                        latestDiagnosis.status === 'normal'
                          ? 'glass-pill-ok'
                          : 'glass-pill-critical'
                      }`}
                    >
                      {latestDiagnosis.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Confidence: {Math.round(latestDiagnosis.confidence_score * 100)}%
                    </span>
                  </div>
                  <h4 className="text-base font-semibold text-slate-100 mt-2">
                    {latestDiagnosis.primary_fault_name || 'Nominal Operation'}
                  </h4>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {latestDiagnosis.summary}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/[0.08]">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-1.5 font-semibold">
                    Multi-Layer Evidence:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {latestDiagnosis.evidence_items?.map((ev) => (
                      <span
                        key={ev.id}
                        className="glass-pill glass-pill-info capitalize"
                      >
                        {ev.evidence_type}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-400 font-mono">
                No recent diagnoses recorded yet. Run a hybrid analysis from the Diagnostics tab.
              </div>
            )}
          </div>

          {/* Quick Action Navigation */}
          <div className="glass-panel p-5 shadow-2xl">
            <h3 className="text-[10px] font-mono uppercase tracking-widest text-slate-400 mb-3 font-semibold">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <Link
                to="/monitoring"
                className="glass-panel-interactive p-3 flex flex-col gap-1.5 transition-all"
              >
                <div className="p-1.5 rounded-lg bg-cyan-400/10 text-cyan-400 w-fit">
                  <Radio className="w-4 h-4" />
                </div>
                <span className="font-semibold text-slate-100">Sensor Plots</span>
                <span className="text-[10px] text-slate-400">Live telemetry stream</span>
              </Link>
              <Link
                to="/maintenance"
                className="glass-panel-interactive p-3 flex flex-col gap-1.5 transition-all"
              >
                <div className="p-1.5 rounded-lg bg-amber-400/10 text-amber-400 w-fit">
                  <Wrench className="w-4 h-4" />
                </div>
                <span className="font-semibold text-slate-100">Work Orders</span>
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
