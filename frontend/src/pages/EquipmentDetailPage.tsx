import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Cpu, Radio, Settings, Wrench } from 'lucide-react'
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

  // Fetch Components
  // Fetch Sensors
  const { data: sensors = [] } = useQuery({
    queryKey: ['sensors', id],
    queryFn: () => api.get<Sensor[]>(`/equipment/${id}/sensors`),
    enabled: !!id,
  })

  if (isLoading || !equipment) {
    return (
      <div className="p-12 text-center font-mono text-slate-400">
        Loading equipment telemetry...
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
            className="rounded-lg border border-slate-800 bg-slate-900 p-2 text-slate-400 transition-colors hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded border border-cyan-800 bg-cyan-950 px-2 py-0.5 font-mono text-xs font-semibold text-cyan-300">
                {equipment.asset_tag}
              </span>
              <h2 className="text-xl font-bold tracking-tight text-white">{equipment.name}</h2>
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
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-500"
          >
            <Cpu className="h-3.5 w-3.5" />
            Run Diagnosis
          </Link>
          <Link
            to="/maintenance"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700"
          >
            <Wrench className="h-3.5 w-3.5" />
            Create Work Order
          </Link>
        </div>
      </div>

      {/* 3D Model Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">
              Interactive 3D Component Inspection
            </h3>
            <p className="mt-0.5 text-xs text-slate-400">
              Click individual components to view sensor status, inspect drive-end bearings, or
              isolate stator coils.
            </p>
          </div>
          <button
            onClick={() => setExplodedView(!explodedView)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 font-mono text-xs text-cyan-300 transition-colors hover:bg-slate-700"
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
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Specification */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
            <Settings className="h-4 w-4 text-cyan-400" />
            Nameplate Specifications
          </h3>
          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            {Object.entries(equipment.specification || {}).map(([key, value]) => (
              <div key={key} className="rounded border border-slate-800 bg-slate-950/60 p-2.5">
                <span className="block text-[10px] text-slate-500 uppercase">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-semibold text-slate-200">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Installed Sensors */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
            <Radio className="h-4 w-4 text-cyan-400" />
            Condition Monitoring Sensors ({sensors.length})
          </h3>
          <div className="space-y-2">
            {sensors.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 p-3 font-mono text-xs"
              >
                <div>
                  <span className="block font-semibold text-slate-200">{s.sensor_key}</span>
                  <span className="text-[10px] text-slate-500 uppercase">
                    Type: {s.measurement_type} • Unit: {s.unit}
                  </span>
                </div>
                <span className="rounded border border-emerald-800 bg-emerald-950 px-2 py-0.5 text-[10px] text-emerald-400">
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
