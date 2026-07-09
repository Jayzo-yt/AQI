'use client'

import { useState } from 'react'
import Link from 'next/link'
import { EndpointConsole } from '@/components/EndpointConsole'

export default function EndpointsPage() {
  const [selectedDate, setSelectedDate] = useState('2020-01-15')
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null)

  return (
    <div className="min-h-screen bg-mission-bg text-white">
      <div className="border-b border-white/5 bg-mission-panel/80 backdrop-blur-[16px]">
        <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-6 py-5">
          <div>
            <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-400">API CONSOLE</div>
            <h1 className="mt-1 text-xl font-semibold tracking-[0.18em] text-white">Backend endpoint explorer</h1>
          </div>
          <Link
            href="/"
            className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-200 transition-colors hover:bg-white/10 hover:text-white"
          >
            Back to dashboard
          </Link>
        </div>
      </div>

      <div className="mx-auto grid w-full max-w-[1600px] gap-6 px-6 py-6 lg:grid-cols-[1fr_380px]">
        <section className="rounded-3xl border border-white/5 bg-[#0C1117] p-6 shadow-panel">
          <div className="max-w-2xl space-y-4">
            <div className="text-[11px] font-semibold tracking-[0.18em] text-sky-300">SEPARATE ROUTE</div>
            <h2 className="text-3xl font-semibold text-white">Use the console without covering the map</h2>
            <p className="text-sm leading-7 text-slate-400">
              This page keeps the dashboard map clean while still exposing the full backend surface for testing and inspection.
              The console can preview health, stations, cities, hotspots, predictions, statistics, methodology, model performance,
              and AQI grid/image routes.
            </p>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">DEFAULT DATE</div>
                <div className="mt-2 text-lg text-white">{selectedDate}</div>
              </div>
              <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                <div className="text-[10px] font-semibold tracking-[0.16em] text-slate-500">LOCATION</div>
                <div className="mt-2 text-lg text-white">{selectedLocation ? `${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lng.toFixed(4)}` : 'None selected'}</div>
              </div>
            </div>

            <div className="rounded-3xl border border-white/5 bg-gradient-to-br from-white/5 to-transparent p-5 text-sm leading-7 text-slate-400">
              Use the cards in the console to inspect each backend route, then click hotspot rows to populate a prediction location.
              The standalone page is intentionally separate from the mission map so the dashboard layout stays visible at all times.
            </div>
          </div>
        </section>

        <div className="relative min-h-[760px]">
          <EndpointConsole
            selectedDate={selectedDate}
            selectedLocation={selectedLocation}
            onFocusLocation={setSelectedLocation}
          />
        </div>
      </div>
    </div>
  )
}
