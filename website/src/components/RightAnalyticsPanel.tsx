'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff } from 'lucide-react'
import { API_BASE_URL } from '@/lib/api'

interface RightAnalyticsPanelProps {
  selectedDate: string
  aqiLayer: boolean
  onAqiLayerToggle: (visible: boolean) => void
}

export function RightAnalyticsPanel({
  selectedDate,
  aqiLayer,
  onAqiLayerToggle,
}: RightAnalyticsPanelProps) {
  const [stats, setStats] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'distribution'>('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true)
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/statistics?date=${selectedDate}&resolution=fast`
        )
        const data = await response.json()
        setStats(data.national_stats)
      } catch (error) {
        console.error('Error fetching statistics:', error)
        setStats(null)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [selectedDate])

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Good': '#3CD96B',
      'Satisfactory': '#92D050',
      'Moderately Polluted': '#FFC84A',
      'Poor': '#FF9900',
      'Very Poor': '#FF5E57',
      'Severe': '#C026D3',
    }
    return colors[category] || '#64748b'
  }

  return (
    <motion.div
      className="w-72 bg-mission-panel/95 backdrop-blur-[16px] border-l border-white/5 flex flex-col overflow-hidden z-40 shadow-panel"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {/* Header */}
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center justify-between">
          <h2 className="text-[11px] font-semibold tracking-[0.15em] text-slate-300">ANALYTICS</h2>
          <button
            onClick={() => onAqiLayerToggle(!aqiLayer)}
            className="p-1.5 hover:bg-mission-secondary rounded-md border border-transparent hover:border-white/5 transition-all"
            title="Toggle AQI layer"
          >
            {aqiLayer ? (
              <Eye size={14} className="text-mission-accent" />
            ) : (
              <EyeOff size={14} className="text-slate-500" />
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5">
        {['overview', 'distribution'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`flex-1 py-3 text-[11px] font-semibold tracking-[0.15em] transition-all ${
              activeTab === tab
                ? 'text-mission-accent border-b-2 border-mission-accent bg-mission-secondary/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-mission-secondary/10'
            }`}
          >
            {tab === 'overview' ? 'OVERVIEW' : 'DISTRIBUTION'}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5">
        {loading && (
          <div className="text-center text-slate-500 text-xs font-medium py-8">Loading analytics...</div>
        )}

        {!loading && !stats && (
          <div className="text-center text-slate-500 text-xs font-medium py-8">
            Analytics unavailable for this date.
          </div>
        )}

        {activeTab === 'overview' && stats && (
          <motion.div className="space-y-3.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all group">
              <p className="text-[11px] font-semibold text-slate-400 mb-1 tracking-wide group-hover:text-slate-300 transition-colors">AVERAGE AQI</p>
              <p className="text-[28px] font-medium text-white">{stats.average_aqi}</p>
            </div>

            <div className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all group">
              <p className="text-[11px] font-semibold text-slate-400 mb-1 tracking-wide group-hover:text-slate-300 transition-colors">MAXIMUM AQI</p>
              <p className="text-[28px] font-medium text-white">{stats.maximum_aqi}</p>
            </div>

            <div className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all group">
              <p className="text-[11px] font-semibold text-slate-400 mb-1 tracking-wide group-hover:text-slate-300 transition-colors">MINIMUM AQI</p>
              <p className="text-[28px] font-medium text-white">{stats.minimum_aqi}</p>
            </div>

            <div className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all group">
              <p className="text-[11px] font-semibold text-slate-400 mb-1 tracking-wide group-hover:text-slate-300 transition-colors">AVG PM2.5 (µg/m³)</p>
              <p className="text-[28px] font-medium text-white">{stats.average_pm25}</p>
            </div>

            <div className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all group">
              <p className="text-[11px] font-semibold text-slate-400 mb-1 tracking-wide group-hover:text-slate-300 transition-colors">MONITORING POINTS</p>
              <p className="text-[28px] font-medium text-white">{stats.total_monitoring_points}</p>
            </div>
          </motion.div>
        )}

        {activeTab === 'distribution' && stats && (
          <motion.div className="space-y-3.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {Object.entries(stats.aqi_distribution).map(([category, percentage]: [string, any]) => (
              <div key={category} className="glass-inner p-4 rounded-xl hover:border-white/10 hover:bg-mission-secondary/80 transition-all">
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-xs font-medium text-slate-300">{category}</span>
                  <span className="text-xs font-semibold text-white">{(percentage as number).toFixed(1)}%</span>
                </div>
                <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                  <div
                    className="h-full rounded-full shadow-[0_0_8px_currentColor] transition-all duration-1000"
                    style={{ width: `${percentage}%`, backgroundColor: getCategoryColor(category), color: getCategoryColor(category) }}
                  />
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 text-[10px] text-slate-500 font-medium bg-black/20 flex flex-col gap-1">
        <p>Date: {selectedDate}</p>
        <p>Last update: {stats?.last_update ? new Date(stats.last_update).toLocaleTimeString() : new Date().toLocaleTimeString()}</p>
      </div>
    </motion.div>
  )
}
