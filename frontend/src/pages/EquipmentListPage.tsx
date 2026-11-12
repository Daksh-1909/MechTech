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
          <h2 className="text-xl font-bold text-white tracking-tight">Monitored Equipment Fleet</h2>
          <p className="text-xs text-slate-400 mt-1">
            Electric motors and industrial rotating machinery registered for condition monitoring.
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
              className="pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-56"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Statuses</option>
            <option value="operational">Operational</option>
            <option value="maintenance">Maintenance</option>
            <option value="out_of_service">Out of Service</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-sm font-mono">Loading equipment registry...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
          No equipment found matching criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="rounded-xl bg-slate-900/90 border border-slate-800 p-5 flex flex-col justify-between hover:border-slate-700 transition-all shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-semibold">
                    {item.asset_tag}
                  </span>
                  <span
                    className={`text-[11px] font-mono px-2 py-0.5 rounded-full capitalize font-semibold ${
                      item.status === 'operational'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}
                  >
                    {item.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="text-base font-semibold text-white tracking-tight">{item.name}</h3>
                <p className="text-xs text-slate-400 mt-1">
                  {item.manufacturer || 'ABB'} • {item.model_number || 'Three-Phase Induction Motor'}
                </p>

                {item.specification && (
                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs font-mono bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-slate-500 block text-[10px]">RATED POWER</span>
                      <span className="text-slate-200">{item.specification.rated_power_kw || 7.5} kW</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">RATED SPEED</span>
                      <span className="text-slate-200">{item.specification.rated_speed_rpm || 1450} RPM</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">
                  {item.location_label || 'Plant 1'}
                </span>
                <Link
                  to={`/equipment/${item.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  View Details & 3D <ArrowRight className="w-3.5 h-3.5" />
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

