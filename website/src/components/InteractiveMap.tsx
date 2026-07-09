'use client'

import { useEffect, useRef, useState } from 'react'
import L, { CircleMarker, ImageOverlay, Map as LeafletMap, LatLngTuple } from 'leaflet'
import 'leaflet.heat'
import { API_BASE_URL } from '@/lib/api'

interface InteractiveMapProps {
  selectedDate: string
  selectedLocation: { lat: number; lng: number } | null
  aqiLayer: boolean
  onLocationClick: (location: { lat: number; lng: number }) => void
}

const INDIA_BOUNDS: [LatLngTuple, LatLngTuple] = [
  [8, 68],
  [37, 97.5],
]

const MAP_RENDER_VERSION = 'v4'

const AQI_LEGEND = [
  { label: 'Good', range: '0–50', color: '#00B050' },
  { label: 'Satisfactory', range: '51–100', color: '#92D050' },
  { label: 'Moderate', range: '101–200', color: '#FFFF00' },
  { label: 'Poor', range: '201–300', color: '#FF9900' },
  { label: 'Very Poor', range: '301–400', color: '#FF0000' },
  { label: 'Severe', range: '401+', color: '#99004C' },
]

const BASE_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
const LABEL_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png'

export default function InteractiveMap({
  selectedDate,
  selectedLocation,
  aqiLayer,
  onLocationClick,
}: InteractiveMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<LeafletMap | null>(null)
  const overlayRef = useRef<ImageOverlay | null>(null)
  const markerRef = useRef<CircleMarker | null>(null)
  const haloRef = useRef<CircleMarker | null>(null)
  const onLocationClickRef = useRef(onLocationClick)
  const [gridLoading, setGridLoading] = useState(false)
  const [extractionStatus, setExtractionStatus] = useState('')
  const [extractionError, setExtractionError] = useState('')
  const [overlayReady, setOverlayReady] = useState(false)
  const [overlayMode, setOverlayMode] = useState<'image' | 'grid'>('image')
  const [gridPoints, setGridPoints] = useState<Array<{ latitude: number; longitude: number; aqi: number }>>([])
  const [resolution, setResolution] = useState<'fast' | 'high'>('fast')
  const [overlayOpacity, setOverlayOpacity] = useState(0.62)
  const fallbackLayerRef = useRef<L.Layer | null>(null)

  onLocationClickRef.current = onLocationClick

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    map.current = L.map(mapContainer.current, {
      zoomControl: false,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 12,
      maxBounds: [
        [5, 65],
        [40, 100],
      ],
      maxBoundsViscosity: 0.85,
    }).setView([22.5, 79.5] as LatLngTuple, 5)

    map.current.createPane('aqiPane')
    const aqiPane = map.current.getPane('aqiPane')
    if (aqiPane) {
      aqiPane.style.zIndex = '420'
    }

    map.current.createPane('labelPane')
    const labelPane = map.current.getPane('labelPane')
    if (labelPane) {
      labelPane.style.zIndex = '520'
      labelPane.style.pointerEvents = 'none'
    }

    L.tileLayer(BASE_TILE_URL, {
      attribution: '© OpenStreetMap · © CARTO',
      subdomains: 'abcd',
      maxZoom: 20,
    }).addTo(map.current)

    L.tileLayer(LABEL_TILE_URL, {
      subdomains: 'abcd',
      maxZoom: 20,
      pane: 'labelPane',
      opacity: 0.95,
    }).addTo(map.current)

    L.control.zoom({ position: 'bottomright' }).addTo(map.current)
    L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map.current)

    map.current.on('click', (event: L.LeafletMouseEvent) => {
      onLocationClickRef.current({
        lat: event.latlng.lat,
        lng: event.latlng.lng,
      })
    })

    const resizeObserver = new ResizeObserver(() => {
      map.current?.invalidateSize()
    })
    resizeObserver.observe(mapContainer.current)

    requestAnimationFrame(() => {
      map.current?.invalidateSize()
    })

    return () => {
      resizeObserver.disconnect()
      overlayRef.current?.remove()
      overlayRef.current = null
      markerRef.current?.remove()
      markerRef.current = null
      haloRef.current?.remove()
      haloRef.current = null
      map.current?.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    if (!map.current) return

    markerRef.current?.remove()
    markerRef.current = null
    haloRef.current?.remove()
    haloRef.current = null

    if (!selectedLocation) return

    haloRef.current = L.circleMarker([selectedLocation.lat, selectedLocation.lng], {
      radius: 14,
      fillColor: '#38bdf8',
      color: '#ffffff',
      weight: 2,
      opacity: 0.95,
      fillOpacity: 0.18,
    }).addTo(map.current)

    markerRef.current = L.circleMarker([selectedLocation.lat, selectedLocation.lng], {
      radius: 6,
      fillColor: '#38bdf8',
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95,
    }).addTo(map.current)

    markerRef.current.bindTooltip(
      `${selectedLocation.lat.toFixed(2)}°N, ${selectedLocation.lng.toFixed(2)}°E`,
      {
        permanent: false,
        direction: 'top',
        offset: [0, -8],
        className: 'map-location-tooltip',
      }
    )

    map.current.setView(
      [selectedLocation.lat, selectedLocation.lng],
      Math.max(map.current.getZoom(), 7),
      { animate: true }
    )
  }, [selectedLocation])

  useEffect(() => {
    const controller = new AbortController()

    async function ensureGridExists() {
      setGridLoading(true)
      setOverlayReady(false)
      setExtractionStatus('')
      setExtractionError('')

      try {
        const checkResponse = await fetch(
          `${API_BASE_URL}/api/check-grid?date=${selectedDate}&resolution=${resolution}`,
          { signal: controller.signal }
        )
        const checkData = await checkResponse.json()

        if (!checkData.grid_exists) {
          setExtractionStatus('Grid not found. Starting GEE extraction...')

          const extractResponse = await fetch(
            `${API_BASE_URL}/api/extract-grid?date=${selectedDate}&resolution=${resolution}`,
            { method: 'POST', signal: controller.signal }
          )
          const extractData = await extractResponse.json()

          if (extractData.status === 'queued' || extractData.status === 'already_running') {
            setExtractionStatus('Extraction in progress. This may take a few minutes...')

            let isComplete = false
            let pollCount = 0
            const maxPolls = 360

            while (!isComplete && pollCount < maxPolls && !controller.signal.aborted) {
              await new Promise((resolve) => setTimeout(resolve, 10000))

              const statusResponse = await fetch(
                `${API_BASE_URL}/api/extraction-status/${selectedDate}?resolution=${resolution}`,
                { signal: controller.signal }
              )
              const statusData = await statusResponse.json()

              if (statusData.status === 'completed') {
                isComplete = true
                setExtractionStatus('Extraction complete. Rendering map...')
              } else if (
                statusData.status === 'failed' ||
                statusData.status === 'error' ||
                statusData.status === 'timeout'
              ) {
                setExtractionError(`Extraction failed: ${statusData.error || 'Unknown error'}`)
                return
              } else {
                setExtractionStatus(`Extraction in progress (${statusData.progress ?? 0}%)...`)
              }

              pollCount++
            }

            if (pollCount >= maxPolls) {
              setExtractionError('Extraction took too long. Please check the backend logs.')
              return
            }
          }
        }

        const warmupResponse = await fetch(
          `${API_BASE_URL}/api/aqi-map-image?date=${selectedDate}&resolution=${resolution}&render=${MAP_RENDER_VERSION}`,
          { signal: controller.signal }
        )
        if (!warmupResponse.ok) {
          setExtractionStatus('Raster image unavailable. Loading grid layer fallback...')

          const gridResponse = await fetch(
            `${API_BASE_URL}/api/aqi-grid?date=${selectedDate}&resolution=${resolution}`,
            { signal: controller.signal }
          )

          if (!gridResponse.ok) {
            throw new Error(`Failed to load AQI grid fallback: ${gridResponse.status}`)
          }

          const gridData = await gridResponse.json()
          setGridPoints((gridData.points || []).map((point: { latitude: number; longitude: number; aqi: number }) => ({
            latitude: point.latitude,
            longitude: point.longitude,
            aqi: point.aqi,
          })))
          setOverlayMode('grid')
          setOverlayReady(true)
          return
        }

        if (!controller.signal.aborted) {
          setExtractionStatus('')
          setOverlayMode('image')
          setOverlayReady(true)
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === 'AbortError')) {
          console.error('Failed to prepare AQI map overlay:', error)
          setExtractionError(error instanceof Error ? error.message : 'Unknown error')
        }
      } finally {
        if (!controller.signal.aborted) {
          setGridLoading(false)
        }
      }
    }

    ensureGridExists()

    return () => {
      controller.abort()
    }
  }, [selectedDate, resolution])

  useEffect(() => {
    if (!map.current || !aqiLayer || !overlayReady) {
      overlayRef.current?.remove()
      overlayRef.current = null
      fallbackLayerRef.current?.remove()
      fallbackLayerRef.current = null
      return
    }

    overlayRef.current?.remove()
    overlayRef.current = null
    fallbackLayerRef.current?.remove()
    fallbackLayerRef.current = null

    if (overlayMode === 'grid') {
      const heatData = gridPoints.map((point) => [
        point.latitude,
        point.longitude,
        Math.max(0.15, Math.min(1, point.aqi / 500)),
      ])

      const heatLayer = (L as any).heatLayer(heatData, {
        radius: resolution === 'high' ? 26 : 20,
        blur: resolution === 'high' ? 22 : 16,
        maxZoom: 8,
        minOpacity: overlayOpacity,
        gradient: {
          0.1: '#00B050',
          0.3: '#92D050',
          0.5: '#FFFF00',
          0.7: '#FF9900',
          0.85: '#FF0000',
          1.0: '#99004C',
        },
      })

      heatLayer.addTo(map.current)
      fallbackLayerRef.current = heatLayer

      return () => {
        heatLayer.remove()
        if (fallbackLayerRef.current === heatLayer) {
          fallbackLayerRef.current = null
        }
      }
    }

    // Append timestamp to force reload if the image was regenerated
    const imageUrl = `${API_BASE_URL}/api/aqi-map-image?date=${selectedDate}&resolution=${resolution}&render=${MAP_RENDER_VERSION}&t=${Date.now()}`

    const layer = L.imageOverlay(imageUrl, INDIA_BOUNDS, {
      opacity: overlayOpacity,
      interactive: false,
      pane: 'aqiPane',
      className: 'aqi-surface-overlay',
    })

    layer.addTo(map.current)
    overlayRef.current = layer

    return () => {
      layer.remove()
      if (overlayRef.current === layer) {
        overlayRef.current = null
      }
    }
  }, [aqiLayer, selectedDate, resolution, overlayReady, overlayOpacity, overlayMode, gridPoints])

  return (
    <div className="relative h-full w-full min-h-[420px] bg-[#0b1018]">
      <div ref={mapContainer} className="absolute inset-0 z-0 map-shell" />

      <div className="pointer-events-none absolute left-6 top-6 z-[1000] w-[min(100%,320px)] rounded-2xl border border-white/5 bg-mission-panel/90 px-5 py-4 text-[11px] text-white shadow-panel backdrop-blur-[16px]">
        <div className="font-semibold tracking-[0.15em] text-slate-200 drop-shadow-sm">NATIONWIDE AQI SURFACE</div>
        <div className="mt-1 text-[10px] text-slate-400 font-medium">
          CPCB scale · satellite features + ML predictions
        </div>

        <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-2">
          {AQI_LEGEND.map((item) => (
            <div key={item.label} className="flex items-center gap-2.5 text-slate-300 font-medium">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-[3px] border border-white/10 shadow-[0_2px_4px_rgba(0,0,0,0.4)]"
                style={{ backgroundColor: item.color }}
              />
              <span className="truncate">
                {item.label}
                <span className="text-slate-500"> ({item.range})</span>
              </span>
            </div>
          ))}
        </div>

        <div className="pointer-events-auto mt-4 space-y-3 border-t border-white/5 pt-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-slate-300 font-medium">Layer opacity</span>
            <span className="tabular-nums text-slate-400 font-medium">{Math.round(overlayOpacity * 100)}%</span>
          </div>
          <input
            type="range"
            min={25}
            max={90}
            value={Math.round(overlayOpacity * 100)}
            onChange={(event) => setOverlayOpacity(Number(event.target.value) / 100)}
            className="map-opacity-slider w-full"
          />

          <div className="flex items-center justify-between gap-2 pt-1">
            <span className="text-slate-300 font-medium">Resolution</span>
            <select
              value={resolution}
              onChange={(event) => setResolution(event.target.value as 'fast' | 'high')}
              className="rounded-lg border border-white/5 bg-mission-secondary px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-mission-accent/50 focus:ring-1 focus:ring-mission-accent/30 transition-all cursor-pointer"
            >
              <option value="fast">Fast (1.0°)</option>
              <option value="high">High (0.25°)</option>
            </select>
          </div>
        </div>

        {gridLoading && (
          <div className="mt-2 text-[10px] text-sky-300">
            {extractionStatus || 'Loading nationwide layer...'}
          </div>
        )}
        {extractionError && (
          <div className="mt-2 text-[10px] text-red-400">Error: {extractionError}</div>
        )}
      </div>
    </div>
  )
}
