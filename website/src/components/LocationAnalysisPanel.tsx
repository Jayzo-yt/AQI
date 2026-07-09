'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { X, Loader, ChevronDown, ChevronUp } from 'lucide-react'
import { API_BASE_URL } from '@/lib/api'

interface LocationAnalysisPanelProps {
  location: { lat: number; lng: number }
  date: string
  onClose: () => void
}

export function LocationAnalysisPanel({
  location,
  date,
  onClose,
}: LocationAnalysisPanelProps) {
  const [prediction, setPrediction] = useState<any>(null)
  const [features, setFeatures] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const fetchPrediction = async () => {
      setLoading(true)
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/predict?latitude=${location.lat}&longitude=${location.lng}&date=${date}&resolution=fast`
        )
        const data = await response.json()
        setPrediction(data)

        const featuresResponse = await fetch(`${API_BASE_URL}/api/feature-importance`)
        const featuresData = await featuresResponse.json()
        setFeatures(featuresData.feature_importance || [])
      } catch (error) {
        console.error('Error fetching prediction:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPrediction()
  }, [location, date])

  const getAqiBadgeColor = (category: string) => {
    const colors: Record<string, string> = {
      'Good': 'bg-[#3CD96B]',
      'Satisfactory': 'bg-[#92D050]',
      'Moderately Polluted': 'bg-[#FFC84A]',
      'Poor': 'bg-[#FF9900]',
      'Very Poor': 'bg-[#FF5E57]',
      'Severe': 'bg-[#C026D3]',
    }
    return colors[category] || 'bg-slate-500'
  }

  return (
    <>
      {!isOpen ? (
        <motion.button
          type="button"
          onClick={() => setIsOpen(true)}
          className="absolute top-24 right-6 z-20 rounded-full border border-white/10 bg-mission-panel/90 px-4 py-2 text-[11px] font-semibold tracking-[0.18em] text-slate-200 shadow-panel backdrop-blur-[16px] transition-colors hover:bg-white/10 hover:text-white"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          OPEN LOCATION ANALYSIS
        </motion.button>
      ) : (
        <motion.div
          className="absolute top-24 right-6 z-20 w-[320px] max-h-[calc(100vh-9rem)] overflow-hidden rounded-2xl border border-white/5 bg-mission-panel/95 shadow-panel backdrop-blur-[16px]"
          initial={{ opacity: 0, scale: 0.96, x: 10 }}
          animate={{ opacity: 1, scale: 1, x: 0 }}
          exit={{ opacity: 0, scale: 0.96, x: 10 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
        >
          <div className="flex items-start justify-between gap-3 border-b border-white/5 p-4">
            <div>
              <h3 className="text-[11px] font-semibold tracking-[0.15em] text-slate-300 drop-shadow-sm">LOCATION ANALYSIS</h3>
              <p className="mt-1.5 text-[11px] font-medium text-slate-500">
                Lat: {location.lat.toFixed(4)}, Lng: {location.lng.toFixed(4)}
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-md border border-white/5 p-1.5 transition-all hover:border-white/10 hover:bg-mission-secondary"
                aria-label="Minimize location analysis"
              >
                <ChevronUp size={14} className="text-slate-400" />
              </button>
              <button
                onClick={onClose}
                className="group rounded-md border border-transparent p-1.5 transition-all hover:border-mission-danger/50 hover:bg-mission-danger/20"
                aria-label="Close location analysis"
              >
                <X size={14} className="text-slate-400 transition-colors group-hover:text-mission-danger" />
              </button>
            </div>
          </div>

          <div className="max-h-[calc(100vh-14rem)] space-y-5 overflow-y-auto p-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader size={20} className="text-slate-500 animate-spin" />
              </div>
            ) : prediction ? (
              <>
                <div className="space-y-2">
                  <p className="text-[10px] font-semibold tracking-wider text-slate-400">AIR QUALITY INDEX</p>
                  <div className="flex items-end gap-4">
                    <div className={`${getAqiBadgeColor(prediction.category)} flex-1 rounded-xl p-5 shadow-[inset_0_0_20px_rgba(255,255,255,0.2)]`}>
                      <div className="text-[32px] font-medium leading-none text-white drop-shadow-md">{prediction.aqi}</div>
                      <div className="mt-2 text-[11px] font-semibold uppercase tracking-[0.05em] text-white/90">{prediction.category}</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] font-semibold tracking-wider text-slate-400">PM2.5 CONCENTRATION</p>
                  <div className="glass-inner rounded-xl border border-white/5 bg-black/20 p-4">
                    <div className="text-[24px] font-medium leading-none text-white">
                      {prediction.pm25} <span className="ml-1 text-[13px] font-normal text-slate-400">µg/m³</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 pt-2">
                  <p className="text-[10px] font-semibold tracking-wider text-slate-400">TOP CONTRIBUTING FACTORS</p>
                  <div className="space-y-3">
                    {features.slice(0, 5).map((feat) => (
                      <div key={feat.feature} className="flex items-center justify-between gap-3">
                        <span className="text-[11px] font-medium text-slate-300">{feat.feature}</span>
                        <div className="h-1.5 w-24 overflow-hidden rounded-full border border-white/5 bg-black/40">
                          <div
                            className="h-full rounded-full bg-mission-accent shadow-[0_0_8px_rgba(46,168,255,0.8)]"
                            style={{ width: `${feat.importance}%` }}
                          />
                        </div>
                        <span className="w-8 text-right text-[10px] font-medium text-slate-400">{feat.importance.toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="-mx-4 mb-[-16px] space-y-1.5 border-t border-white/5 bg-black/20 px-4 pb-4 pt-4 text-[10px] font-medium text-slate-500">
                  <p>Selected date: {date}</p>
                  {prediction.region && <p>Grid region: {prediction.region}</p>}
                  {prediction.grid_latitude !== undefined && (
                    <p>
                      Nearest grid cell: {prediction.grid_latitude.toFixed(2)}, {prediction.grid_longitude.toFixed(2)}
                    </p>
                  )}
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-xs font-medium text-slate-500">Unable to fetch prediction</div>
            )}
          </div>
        </motion.div>
      )}
    </>
  )
}
