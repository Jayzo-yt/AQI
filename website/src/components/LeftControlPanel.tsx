'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, MapPin } from 'lucide-react'
import { API_BASE_URL } from '@/lib/api'

interface City {
  name: string
  state: string
  latitude: number
  longitude: number
  station_count: number
}

interface LeftControlPanelProps {
  onLocationSelect: (location: { lat: number; lng: number }) => void
  aqiLayer: boolean
  onAqiLayerToggle: (visible: boolean) => void
  demoTrajectory: boolean
  onDemoTrajectoryToggle: (visible: boolean) => void
  demoUncertainty: boolean
  onDemoUncertaintyToggle: (visible: boolean) => void
  demoSplitView: boolean
  onDemoSplitViewToggle: (visible: boolean) => void
}

export function LeftControlPanel({
  onLocationSelect,
  aqiLayer,
  onAqiLayerToggle,
  demoTrajectory,
  onDemoTrajectoryToggle,
  demoUncertainty,
  onDemoUncertaintyToggle,
  demoSplitView,
  onDemoSplitViewToggle,
}: LeftControlPanelProps) {
  const [cities, setCities] = useState<City[]>([])
  const [filteredCities, setFilteredCities] = useState<City[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/cities`)
        const data = await response.json()
        
        // Group cities by name and state since backend returns station-level granularity
        const groupedCities = new Map<string, City>();
        (data.cities || []).forEach((city: City) => {
          const key = `${city.name}-${city.state}`;
          if (groupedCities.has(key)) {
            const existing = groupedCities.get(key)!;
            existing.station_count += city.station_count;
          } else {
            groupedCities.set(key, { ...city });
          }
        });
        
        const uniqueCities = Array.from(groupedCities.values());
        setCities(uniqueCities)
        setFilteredCities(uniqueCities)
      } catch (error) {
        console.error('Error fetching cities:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCities()
  }, [])

  useEffect(() => {
    const filtered = cities.filter(
      (city) =>
        city.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        city.state.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredCities(filtered)
  }, [searchTerm, cities])

  return (
    <motion.div
      className="w-72 bg-mission-panel/95 backdrop-blur-[16px] border-r border-white/5 flex flex-col overflow-hidden z-40 shadow-panel"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div className="p-5 border-b border-white/5">
        <h2 className="text-[11px] font-semibold tracking-[0.15em] text-slate-300 mb-3">CITY SEARCH</h2>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search locations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 bg-mission-secondary/60 border border-white/5 rounded-lg text-[13px] text-white placeholder-slate-500 focus:outline-none focus:border-mission-accent/50 focus:bg-mission-secondary transition-all"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-3 space-y-1">
          {loading ? (
            <div className="p-4 text-center text-slate-500 text-xs font-medium">Loading cities...</div>
          ) : filteredCities.length > 0 ? (
            filteredCities.map((city, idx) => (
              <motion.button
                key={`${city.name}-${city.state}`}
                onClick={() => onLocationSelect({ lat: city.latitude, lng: city.longitude })}
                className="w-full text-left p-3 rounded-xl border border-transparent hover:bg-mission-secondary hover:border-white/5 transition-all group"
                whileHover={{ x: 4 }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.05 }}
              >
                <div className="flex items-start gap-2.5">
                  <MapPin size={14} className="text-slate-500 group-hover:text-mission-accent mt-0.5 flex-shrink-0 transition-colors" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-slate-200 group-hover:text-mission-accent transition-colors truncate">{city.name}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">{city.state}</p>
                    <p className="text-[10px] text-slate-600 mt-1 font-medium">{city.station_count} station{city.station_count > 1 ? 's' : ''}</p>
                  </div>
                </div>
              </motion.button>
            ))
          ) : (
            <div className="p-4 text-center text-slate-500 text-xs font-medium">No cities found</div>
          )}
        </div>
      </div>

      <div className="p-5 border-t border-white/5 space-y-3 bg-black/20">
        <h3 className="text-[11px] font-semibold tracking-[0.15em] text-slate-300">DATA LAYERS</h3>
        <label className="flex items-center gap-3 cursor-pointer group">
          <div className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${aqiLayer ? 'bg-mission-accent border-mission-accent' : 'border-slate-600 bg-transparent'}`}>
            {aqiLayer && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
          </div>
          <input
            type="checkbox"
            checked={aqiLayer}
            onChange={(event) => onAqiLayerToggle(event.target.checked)}
            className="hidden"
          />
          <span className="text-[12px] font-medium text-slate-400 group-hover:text-white transition-colors">AQI Heatmap Layer</span>
        </label>
      </div>

      <div className="p-5 border-t border-white/5 space-y-3 bg-indigo-950/40">
        <h3 className="text-[11px] font-semibold tracking-[0.15em] text-indigo-300">SKYTRACE DEMO FEATURES</h3>
        
        {/* Feature 1: Trajectory */}
        <label className="flex items-center gap-3 cursor-pointer group">
          <div className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${demoTrajectory ? 'bg-indigo-500 border-indigo-500' : 'border-slate-600 bg-transparent'}`}>
            {demoTrajectory && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
          </div>
          <input
            type="checkbox"
            checked={demoTrajectory}
            onChange={(event) => onDemoTrajectoryToggle(event.target.checked)}
            className="hidden"
          />
          <span className="text-[12px] font-medium text-indigo-200 group-hover:text-white transition-colors">1. Fire → City Trajectory Map</span>
        </label>

        {/* Feature 2: Uncertainty */}
        <label className="flex items-center gap-3 cursor-pointer group">
          <div className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${demoUncertainty ? 'bg-indigo-500 border-indigo-500' : 'border-slate-600 bg-transparent'}`}>
            {demoUncertainty && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
          </div>
          <input
            type="checkbox"
            checked={demoUncertainty}
            onChange={(event) => onDemoUncertaintyToggle(event.target.checked)}
            className="hidden"
          />
          <span className="text-[12px] font-medium text-indigo-200 group-hover:text-white transition-colors">2. Kriging Uncertainty Layers</span>
        </label>

        {/* Feature 3: Split View */}
        <label className="flex items-center gap-3 cursor-pointer group">
          <div className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${demoSplitView ? 'bg-indigo-500 border-indigo-500' : 'border-slate-600 bg-transparent'}`}>
            {demoSplitView && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
          </div>
          <input
            type="checkbox"
            checked={demoSplitView}
            onChange={(event) => onDemoSplitViewToggle(event.target.checked)}
            className="hidden"
          />
          <span className="text-[12px] font-medium text-indigo-200 group-hover:text-white transition-colors">3. Dual-Objective Split View</span>
        </label>
      </div>
    </motion.div>
  )
}
