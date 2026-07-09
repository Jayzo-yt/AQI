'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { API_BASE_URL } from '@/lib/api'
import { Activity, BarChart3, Building2, Layers3, MapPinned, Microscope, RefreshCw, Server, Sparkles } from 'lucide-react'

type HealthResponse = {
  status: string
  timestamp: string
  model_loaded: boolean
  data_loaded: boolean
}

type City = {
  name: string
  state: string
  latitude: number
  longitude: number
  station_count: number
}

type Station = {
  id: string
  name: string
  city: string
  state: string
  latitude: number
  longitude: number
  status: string
}

type Hotspot = {
  rank: number
  city: string
  state: string
  latitude: number
  longitude: number
  aqi: number
  pm25: number
  category: string
}

interface EndpointConsoleProps {
  selectedDate: string
  selectedLocation: { lat: number; lng: number } | null
  onFocusLocation: (location: { lat: number; lng: number }) => void
}

const endpointDefinitions = [
  { key: 'health', path: '/health', icon: Activity },
  { key: 'stations', path: '/api/stations', icon: Building2 },
  { key: 'cities', path: '/api/cities', icon: MapPinned },
  { key: 'predict', path: '/api/predict', icon: Sparkles },
  { key: 'hotspots', path: '/api/hotspots', icon: Layers3 },
  { key: 'statistics', path: '/api/statistics', icon: BarChart3 },
  { key: 'time_series', path: '/api/time-series', icon: RefreshCw },
  { key: 'methodology', path: '/api/methodology', icon: Microscope },
  { key: 'model_performance', path: '/api/model-performance', icon: Server },
  { key: 'aqi_grid', path: '/api/aqi-grid', icon: Layers3 },
  { key: 'aqi_map_image', path: '/api/aqi-map-image', icon: MapPinned },
]

export function EndpointConsole({ selectedDate, selectedLocation, onFocusLocation }: EndpointConsoleProps) {
  const [activeTab, setActiveTab] = useState<'status' | 'data' | 'docs'>('status')
  const [expanded, setExpanded] = useState(true)
  const [refreshToken, setRefreshToken] = useState(0)

  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [stations, setStations] = useState<Station[]>([])
  const [cities, setCities] = useState<City[]>([])
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [prediction, setPrediction] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [performance, setPerformance] = useState<any>(null)
  const [methodology, setMethodology] = useState<any>(null)
  const [gridInfo, setGridInfo] = useState<any>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadConsoleData() {
      try {
        const [healthResponse, stationsResponse, citiesResponse, hotspotsResponse, datesResponse, methodologyResponse, performanceResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/health`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/stations`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/cities`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/hotspots?date=${selectedDate}&resolution=fast&top_n=8`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/available-dates`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/methodology`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/api/model-performance`, { signal: controller.signal }),
        ])

        const healthData = await healthResponse.json()
        const stationsData = await stationsResponse.json()
        const citiesData = await citiesResponse.json()
        const hotspotsData = await hotspotsResponse.json()
        const datesData = await datesResponse.json()
        const methodologyData = await methodologyResponse.json()
        const performanceData = await performanceResponse.json()

        setHealth(healthData)
        setStations(stationsData.stations || [])
        setCities(citiesData.cities || [])
        setHotspots(hotspotsData.hotspots || [])
        setAvailableDates(datesData.available_dates || [])
        setMethodology(methodologyData.methodology)
        setPerformance(performanceData.performance)

        if (selectedLocation) {
          const predictionResponse = await fetch(
            `${API_BASE_URL}/api/predict?latitude=${selectedLocation.lat}&longitude=${selectedLocation.lng}&date=${selectedDate}&resolution=fast`,
            { signal: controller.signal }
          )
          const predictionData = await predictionResponse.json()
          setPrediction(predictionData)
        } else {
          setPrediction(null)
        }

        const statisticsResponse = await fetch(
          `${API_BASE_URL}/api/statistics?date=${selectedDate}&resolution=fast`,
          { signal: controller.signal }
        )
        const statisticsData = await statisticsResponse.json()
        setStats(statisticsData.national_stats)

        const gridResponse = await fetch(
          `${API_BASE_URL}/api/aqi-grid?date=${selectedDate}&resolution=fast`,
          { signal: controller.signal }
        )
        if (gridResponse.ok) {
          const gridData = await gridResponse.json()
          setGridInfo(gridData.meta)
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === 'AbortError')) {
          console.error('Failed to load endpoint console data:', error)
        }
      }
    }

    loadConsoleData()
    return () => controller.abort()
  }, [selectedDate, selectedLocation, refreshToken])

  const endpointCards = useMemo(
    () => [
      {
        title: 'Health',
        value: health?.status || 'unknown',
        detail: health ? `Model ${health.model_loaded ? 'loaded' : 'missing'} · Data ${health.data_loaded ? 'loaded' : 'missing'}` : 'Loading...',
      },
      {
        title: 'Stations',
        value: stations.length.toString(),
        detail: 'Monitoring sites with coordinates',
      },
      {
        title: 'Cities',
        value: cities.length.toString(),
        detail: 'Searchable city locations',
      },
      {
        title: 'Hotspots',
        value: hotspots.length.toString(),
        detail: 'Top polluted regions for the date',
      },
      {
        title: 'Dates',
        value: availableDates.length.toString(),
        detail: 'Available timeline frames',
      },
      {
        title: 'Grid points',
        value: gridInfo?.total_points?.toString() || '0',
        detail: 'AQI raster cells for the map layer',
      },
    ],
    [health, stations.length, cities.length, hotspots.length, availableDates.length, gridInfo]
  )

  return (
    <motion.aside
      className="absolute right-4 top-4 bottom-40 z-[1100] w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-3xl border border-white/5 bg-mission-panel/95 shadow-panel backdrop-blur-[18px]"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
        <div>
          <div className="text-[11px] font-semibold tracking-[0.16em] text-slate-200">API ENDPOINT CONSOLE</div>
          <div className="mt-1 text-[10px] text-slate-500">Live frontend coverage for all backend routes</div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setRefreshToken((value) => value + 1)}
            className="rounded-lg border border-white/5 bg-black/20 p-2 text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
            title="Refresh endpoint data"
          >
            <RefreshCw size={14} />
          </button>
          <button
            onClick={() => setExpanded((value) => !value)}
            className="rounded-lg border border-white/5 bg-black/20 px-3 py-1.5 text-[11px] font-medium text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="flex h-full flex-col">
          <div className="flex border-b border-white/5 px-2 pt-2">
            {(['status', 'data', 'docs'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 rounded-t-xl px-3 py-2 text-[11px] font-semibold tracking-[0.16em] transition-colors ${
                  activeTab === tab
                    ? 'bg-white/5 text-white'
                    : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4">
            {activeTab === 'status' && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  {endpointCards.map((card) => (
                    <div key={card.title} className="rounded-2xl border border-white/5 bg-black/20 p-3">
                      <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">{card.title}</div>
                      <div className="mt-2 text-[20px] font-medium text-white">{card.value}</div>
                      <div className="mt-1 text-[10px] leading-relaxed text-slate-500">{card.detail}</div>
                    </div>
                  ))}
                </div>

                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">CURRENT LOCATION</div>
                  <div className="mt-2 text-[12px] text-slate-200">
                    {selectedLocation
                      ? `${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lng.toFixed(4)}`
                      : 'Click the map to generate a prediction'}
                  </div>
                  {prediction && (
                    <div className="mt-3 space-y-1 text-[11px] text-slate-400">
                      <div>Predicted AQI: <span className="text-white">{prediction.aqi}</span></div>
                      <div>Predicted PM2.5: <span className="text-white">{prediction.pm25}</span></div>
                      <div>Region: <span className="text-white">{prediction.region || 'n/a'}</span></div>
                    </div>
                  )}
                  {stats && (
                    <div className="mt-3 grid grid-cols-3 gap-2 text-[10px] text-slate-500">
                      <div className="rounded-xl border border-white/5 bg-white/5 p-2">Avg {stats.average_aqi}</div>
                      <div className="rounded-xl border border-white/5 bg-white/5 p-2">Max {stats.maximum_aqi}</div>
                      <div className="rounded-xl border border-white/5 bg-white/5 p-2">Min {stats.minimum_aqi}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'data' && (
              <div className="space-y-4">
                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="mb-3 text-[10px] font-semibold tracking-[0.16em] text-slate-500">ENDPOINTS</div>
                  <div className="space-y-2">
                    {endpointDefinitions.map((endpoint) => {
                      const Icon = endpoint.icon
                      return (
                        <div key={endpoint.key} className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/5 px-3 py-2">
                          <div className="flex items-center gap-2">
                            <Icon size={14} className="text-sky-300" />
                            <div>
                              <div className="text-[11px] font-medium text-white">{endpoint.path}</div>
                              <div className="text-[10px] text-slate-500">{endpoint.key}</div>
                            </div>
                          </div>
                          <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">live</div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="mb-2 text-[10px] font-semibold tracking-[0.16em] text-slate-500">HOTSPOTS</div>
                  <div className="space-y-2">
                    {hotspots.slice(0, 5).map((hotspot) => (
                      <button
                        key={`${hotspot.city}-${hotspot.rank}`}
                        onClick={() => onFocusLocation({ lat: hotspot.latitude, lng: hotspot.longitude })}
                        className="w-full rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-left transition-colors hover:bg-white/10"
                      >
                        <div className="flex items-center justify-between text-[11px] text-white">
                          <span>#{hotspot.rank} {hotspot.city}</span>
                          <span className="text-slate-400">AQI {hotspot.aqi}</span>
                        </div>
                        <div className="mt-1 text-[10px] text-slate-500">{hotspot.state} · PM2.5 {hotspot.pm25}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'docs' && methodology && performance && (
              <div className="space-y-4">
                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">METHODLOGY</div>
                  <div className="mt-2 text-[13px] font-medium text-white">{methodology.title}</div>
                  <div className="mt-1 text-[11px] text-slate-500">{methodology.subtitle}</div>
                  <div className="mt-3 space-y-2">
                    {methodology.pipeline?.slice(0, 4).map((stage: any) => (
                      <div key={stage.stage} className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-[11px] text-slate-300">
                        <span className="text-white">{stage.stage}.</span> {stage.name}
                        <div className="mt-1 text-slate-500">{stage.description}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">MODEL PERFORMANCE</div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                    <div className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300">RMSE {performance.station_holdout?.rmse}</div>
                    <div className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300">MAE {performance.station_holdout?.mae}</div>
                    <div className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300">R² {performance.station_holdout?.r2}</div>
                    <div className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300">MAPE {performance.station_holdout?.mape}%</div>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">API QUICK LINKS</div>
                  <div className="mt-3 grid grid-cols-1 gap-2 text-[11px] text-slate-300">
                    <a className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 hover:bg-white/10" href={`${API_BASE_URL}/health`} target="_blank" rel="noreferrer">{API_BASE_URL}/health</a>
                    <a className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 hover:bg-white/10" href={`${API_BASE_URL}/api/aqi-map-image?date=${selectedDate}&resolution=fast`} target="_blank" rel="noreferrer">AQI image</a>
                    <a className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 hover:bg-white/10" href={`${API_BASE_URL}/api/aqi-grid?date=${selectedDate}&resolution=fast`} target="_blank" rel="noreferrer">AQI grid</a>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.aside>
  )
}
