import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Cpu,
  Layers,
  Radio,
  Settings,
  Sparkles,
  Wrench,
} from 'lucide-react'
import { api } from '../lib/api'
import type { Component, Equipment, Sensor, SensorReading } from '../types/api'
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

  // Fetch Components
  const { data: components = [] } = useQuery({
    queryKey: ['components', id],
    queryFn: () => api.get<Component[]>(`/equipment/${id}/components`),
    enabled: !!id,
  })

  // Fetch Sensors
  const { data: sensors = [] } = useQuery({
    queryKey: ['sensors', id],
    queryFn: () => api.get<Sensor[]>(`/equipment/${id}/sensors`),
    enabled: !!id,
  })

  if (isLoading || !equipment) {
    return <div className="p-12 text-center text-slate-400 font-mono">Loading equipment telemetry...</div>
  }

  return (
    <div className="space-y-6">
      {/* Back button & Title Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/equipment"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold">
                {equipment.asset_tag}
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">{equipment.name}</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {equipment.manufacturer || 'ABB'} • {equipment.model_number || 'M3AA 132 SMB 4'} • {equipment.location_label || 'Lab Bench 1'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/diagnostics"
            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-blue-600/20"
          >
            <Cpu className="w-3.5 h-3.5" />
            Run Diagnosis
          </Link>
          <Link
            to="/maintenance"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-1.5"
          >
            <Wrench className="w-3.5 h-3.5" />
            Create Work Order
          </Link>
        </div>
      </div>

      {/* 3D Model Card */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-white">Interactive 3D Component Inspection</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Click individual components to view sensor status, inspect drive-end bearings, or isolate stator coils.
            </p>
          </div>
          <button
            onClick={() => setExplodedView(!explodedView)}
            className="px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 transition-colors"
          >
            {explodedView ? 'Collapse Components' : 'Explode Components'}
          </button>
        </div>

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

      {/* Specifications & Sensor Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Specification */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-lg">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Settings className="w-4 h-4 text-cyan-400" />
            Nameplate Specifications
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            {Object.entries(equipment.specification || {}).map(([key, value]) => (
              <div key={key} className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">{key.replace(/_/g, ' ')}</span>
                <span className="text-slate-200 font-semibold">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Installed Sensors */}
        <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 shadow-lg">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            Condition Monitoring Sensors ({sensors.length})
          </h3>
          <div className="space-y-2">
            {sensors.map((s) => (
              <div
                key={s.id}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <span className="text-slate-200 font-semibold block">{s.sensor_key}</span>
                  <span className="text-slate-500 text-[10px] uppercase">
                    Type: {s.measurement_type} • Unit: {s.unit}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">
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

