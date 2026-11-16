import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, Cpu, Filter, Layers, Plus, Search, ShieldAlert } from 'lucide-react'
import { api } from '../lib/api'
import type { Equipment } from '../types/api'

export const EquipmentListPage: React.FC = () => {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: equipment = [], isLoading } = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.get<Equipment[]>('/equipment'),
  })

  const filtered = equipment.filter((eq) => {
    const matchesSearch =
      eq.name.toLowerCase().includes(search.toLowerCase()) ||
      eq.asset_tag.toLowerCase().includes(search.toLowerCase()) ||
      (eq.location_label || '').toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === 'all' || eq.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Monitored Equipment Fleet</span>
            <span className="glass-pill glass-pill-info">{filtered.length} Machines</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Electric induction motors and rotating machinery registered for condition monitoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search tag, name, model..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="glass-input pl-9 w-60"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="glass-input w-40"
          >
            <option value="all" className="bg-slate-900">All Statuses</option>
            <option value="operational" className="bg-slate-900">Operational</option>
            <option value="maintenance" className="bg-slate-900">Maintenance</option>
            <option value="out_of_service" className="bg-slate-900">Out of Service</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-sm font-mono glass-panel">Loading equipment registry...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center glass-panel text-slate-400 text-sm font-mono">
          No equipment found matching search criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="glass-panel-interactive p-5 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="glass-pill glass-pill-info font-bold">
                    {item.asset_tag}
                  </span>
                  <span
                    className={`glass-pill ${
                      item.status === 'operational'
                        ? 'glass-pill-ok'
                        : 'glass-pill-warning'
                    }`}
                  >
                    {item.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white tracking-tight group-hover:text-cyan-300 transition-colors">
                  {item.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {item.manufacturer || 'ABB'} • {item.model_number || 'Three-Phase Induction Motor'}
                </p>

                {item.specification && (
                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs font-mono p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase tracking-wider">RATED POWER</span>
                      <span className="text-slate-200 font-semibold">{item.specification.rated_power_kw || 7.5} kW</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase tracking-wider">RATED SPEED</span>
                      <span className="text-slate-200 font-semibold">{item.specification.rated_speed_rpm || 1450} RPM</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-5 pt-3.5 border-t border-white/[0.08] flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">
                  {item.location_label || 'Plant Bench 1'}
                </span>
                <Link
                  to={`/equipment/${item.id}`}
                  className="glass-btn glass-btn-primary text-xs"
                >
                  <span>Inspect 3D</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default EquipmentListPage
