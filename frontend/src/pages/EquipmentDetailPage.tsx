import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Cpu, Radio, Settings, Wrench, Activity } from 'lucide-react'
import { api } from '../lib/api'
import type { Equipment, Sensor } from '../types/api'
import MotorScene from '../components/motor3d/MotorScene'

export const EquipmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [selectedComponent, setSelectedComponent] = useState<string | null>('bearing_front')
  const [explodedView, setExplodedView] = useState(false)

  // Fetch Equipment
  const { data: equipment, isLoading } = useQuery({
    queryKey: ['equipment', id],
    queryFn: () => api.get<Equipment>(`/equipment/${id}`),
    enabled: !!id,
  })

  // Fetch Sensors
  const { data: sensors = [] } = useQuery({
    queryKey: ['sensors', id],
    queryFn: () => api.get<Sensor[]>(`/equipment/${id}/sensors`),
    enabled: !!id,
  })

  if (isLoading || !equipment) {
    return (
      <div className="glass-panel p-16 text-center font-mono text-slate-300">
        <Activity className="mx-auto mb-3 h-6 w-6 animate-spin text-cyan-400" />
        Loading equipment telemetry & 3D model...
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back button & Title Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/equipment"
            className="glass-panel-interactive flex h-10 w-10 items-center justify-center rounded-xl text-slate-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="glass-pill glass-pill-cyan font-mono text-xs font-semibold">
                {equipment.asset_tag}
              </span>
              <h2 className="text-xl font-bold tracking-tight text-white drop-shadow-sm">
                {equipment.name}
              </h2>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              {equipment.manufacturer || 'ABB'} • {equipment.model_number || 'M3AA 132 SMB 4'} •{' '}
              {equipment.location_label || 'Lab Bench 1'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/diagnostics"
            className="glass-btn-primary flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold"
          >
            <Cpu className="h-3.5 w-3.5" />
            Run Diagnosis
          </Link>
          <Link
            to="/maintenance"
            className="glass-btn flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-200"
          >
            <Wrench className="h-3.5 w-3.5" />
            Create Work Order
          </Link>
        </div>
      </div>

      {/* 3D Model Card */}
      <div className="glass-panel relative overflow-hidden p-6 shadow-2xl">
        <div className="absolute top-0 right-1/4 h-32 w-32 rounded-full bg-cyan-500/10 blur-2xl pointer-events-none" />
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <h3 className="text-sm font-semibold text-white">
                Interactive 3D Component Inspection
              </h3>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              Click individual components to isolate mesh topology, inspect drive-end bearings, or
              view winding status.
            </p>
          </div>
          <button
            onClick={() => setExplodedView(!explodedView)}
            className="glass-btn px-3.5 py-1.5 font-mono text-xs text-cyan-300 hover:text-cyan-200"
          >
            {explodedView ? 'Collapse Components' : 'Explode Components'}
          </button>
        </div>

        <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-950/40">
          <MotorScene
            selectedComponentKey={selectedComponent}
            onSelectComponent={(key) => setSelectedComponent(key)}
            exploded={explodedView}
            componentStatuses={{
              bearing_front: {
                key: 'bearing_front',
                name: 'Drive-End Front Bearing',
                status: 'normal',
                metricLabel: 'RMS Vibration',
                metricValue: '0.14 mm/s',
              },
              stator: {
                key: 'stator',
                name: 'Stator Copper Windings',
                status: 'normal',
                metricLabel: 'Winding Temp',
                metricValue: '58.2 °C',
              },
              cooling_fan: {
                key: 'cooling_fan',
                name: 'Rear Ventilation Fan',
                status: 'normal',
                metricLabel: 'RPM',
                metricValue: '1450',
              },
            }}
          />
        </div>
      </div>

      {/* Specifications & Sensor Table */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Specification */}
        <div className="glass-panel p-5">
          <h3 className="mb-3.5 flex items-center gap-2 text-sm font-semibold text-white">
            <Settings className="h-4 w-4 text-cyan-400" />
            Nameplate Technical Specifications
          </h3>
          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            {Object.entries(equipment.specification || {}).map(([key, value]) => (
              <div
                key={key}
                className="glass-panel-interactive rounded-xl p-3 border border-white/5 bg-slate-950/40"
              >
                <span className="block text-[10px] text-slate-400 uppercase tracking-wider">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-semibold text-slate-100">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Installed Sensors */}
        <div className="glass-panel p-5">
          <h3 className="mb-3.5 flex items-center gap-2 text-sm font-semibold text-white">
            <Radio className="h-4 w-4 text-cyan-400" />
            Condition Monitoring Sensors ({sensors.length})
          </h3>
          <div className="space-y-2.5">
            {sensors.map((s) => (
              <div
                key={s.id}
                className="glass-panel-interactive flex items-center justify-between rounded-xl p-3.5 font-mono text-xs border border-white/5 bg-slate-950/40"
              >
                <div>
                  <span className="block font-semibold text-slate-100">{s.sensor_key}</span>
                  <span className="text-[10px] text-slate-400 uppercase">
                    Type: {s.measurement_type} • Unit: {s.unit}
                  </span>
                </div>
                <span className="glass-pill glass-pill-emerald text-[10px]">
                  Online
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default EquipmentDetailPage
