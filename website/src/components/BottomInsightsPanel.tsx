'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertCircle } from 'lucide-react'
import { API_BASE_URL } from '@/lib/api'

interface Hotspot {
  rank: number
  station_name: string
  city: string
  state: string
  pm25: number
  aqi: number
  category: string
}

interface BottomInsightsPanelProps {
  selectedDate: string
}

export function BottomInsightsPanel({ selectedDate }: BottomInsightsPanelProps) {
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHotspots = async () => {
      setLoading(true)
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/hotspots?date=${selectedDate}&resolution=fast&top_n=10`
        )
        const data = await response.json()
        setHotspots(data.hotspots || [])
      } catch (error) {
        console.error('Error fetching hotspots:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHotspots()
  }, [selectedDate])

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Good': 'text-[#3CD96B] bg-[#3CD96B]/10 border-[#3CD96B]/20',
      'Satisfactory': 'text-[#92D050] bg-[#92D050]/10 border-[#92D050]/20',
      'Moderately Polluted': 'text-[#FFC84A] bg-[#FFC84A]/10 border-[#FFC84A]/20',
      'Poor': 'text-[#FF9900] bg-[#FF9900]/10 border-[#FF9900]/20',
      'Very Poor': 'text-[#FF5E57] bg-[#FF5E57]/10 border-[#FF5E57]/20',
      'Severe': 'text-[#C026D3] bg-[#C026D3]/10 border-[#C026D3]/20',
    }
    return colors[category] || 'text-slate-400 bg-slate-500/10 border-slate-500/20'
  }

  return (
    <motion.div
      className="bg-mission-panel/90 backdrop-blur-[16px] border-t border-white/5 px-8 py-5 overflow-x-auto shadow-panel z-50 relative min-h-[140px]"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
    >
      <div className="flex items-start gap-6">
        {/* Title */}
        <div className="flex-shrink-0 pt-2 w-48">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={15} className="text-mission-danger" />
            <h3 className="text-[11px] font-semibold tracking-[0.15em] text-slate-300">TOP POLLUTION HOTSPOTS</h3>
          </div>
          <p className="text-[11px] font-medium text-slate-500 mt-2">Mission Date: {selectedDate}</p>
        </div>

        {/* Hotspots Carousel */}
        <div className="flex-1 flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
          {loading ? (
            <div className="text-slate-500 text-xs font-medium pt-4">Loading hotspots...</div>
          ) : hotspots.length > 0 ? (
            hotspots.map((hotspot, idx) => (
              <motion.div
                key={`${hotspot.city}-${idx}`}
                className="flex-shrink-0 glass-inner p-4 rounded-xl w-[220px] border border-white/5 cursor-pointer hover:border-white/20 hover:bg-mission-secondary/80 transition-all group relative overflow-hidden"
                whileHover={{ y: -2 }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.05 }}
              >
                <div className="absolute top-0 right-0 w-16 h-16 bg-white/5 rounded-bl-[64px] -z-10 group-hover:bg-white/10 transition-colors" />
                
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <p className="text-[13px] font-semibold text-slate-200 group-hover:text-mission-accent transition-colors truncate max-w-[140px]">
                      {hotspot.city}
                    </p>
                    <p className="text-[11px] text-slate-500 font-medium">{hotspot.state}</p>
                  </div>
                  <span className="text-[10px] font-bold text-slate-500 bg-white/5 px-2 py-0.5 rounded-md flex-shrink-0">#{hotspot.rank}</span>
                </div>

                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-400">AQI</span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${getCategoryColor(
                      hotspot.category
                    )}`}>
                      {hotspot.aqi}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-400">PM2.5</span>
                    <span className="text-[11px] font-medium text-slate-200">{hotspot.pm25} µg/m³</span>
                  </div>
                </div>
              </motion.div>
            ))
          ) : (
            <div className="text-slate-500 text-xs font-medium pt-4">No hotspots available</div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
