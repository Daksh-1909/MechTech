import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Search } from 'lucide-react'
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
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Monitored Equipment Fleet</h2>
          <p className="mt-1 text-xs text-slate-400">
            Electric motors and industrial rotating machinery registered for condition monitoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search tag, name, model..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-56 rounded-lg border border-slate-800 bg-slate-900 py-1.5 pr-3 pl-9 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:border-cyan-500 focus:outline-none"
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
        <div className="p-12 text-center font-mono text-sm text-slate-400">
          Loading equipment registry...
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-12 text-center text-sm text-slate-400">
          No equipment found matching criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg transition-all hover:border-slate-700"
            >
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <span className="rounded border border-cyan-800/60 bg-cyan-950 px-2 py-0.5 font-mono text-xs font-semibold text-cyan-300">
                    {item.asset_tag}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 font-mono text-[11px] font-semibold capitalize ${
                      item.status === 'operational'
                        ? 'border border-emerald-800 bg-emerald-950 text-emerald-400'
                        : 'border border-amber-800 bg-amber-950 text-amber-400'
                    }`}
                  >
                    {item.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="text-base font-semibold tracking-tight text-white">{item.name}</h3>
                <p className="mt-1 text-xs text-slate-400">
                  {item.manufacturer || 'ABB'} •{' '}
                  {item.model_number || 'Three-Phase Induction Motor'}
                </p>

                {item.specification && (
                  <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-slate-800 bg-slate-950/60 p-2.5 font-mono text-xs">
                    <div>
                      <span className="block text-[10px] text-slate-500">RATED POWER</span>
                      <span className="text-slate-200">
                        {item.specification.rated_power_kw || 7.5} kW
                      </span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500">RATED SPEED</span>
                      <span className="text-slate-200">
                        {item.specification.rated_speed_rpm || 1450} RPM
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-slate-800/80 pt-3">
                <span className="font-mono text-[11px] text-slate-400">
                  {item.location_label || 'Plant 1'}
                </span>
                <Link
                  to={`/equipment/${item.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 transition-colors hover:text-cyan-300"
                >
                  View Details & 3D <ArrowRight className="h-3.5 w-3.5" />
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
