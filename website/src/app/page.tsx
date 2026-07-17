'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { TopNavigation } from '@/components/TopNavigation'
import { LeftControlPanel } from '@/components/LeftControlPanel'
import { RightAnalyticsPanel } from '@/components/RightAnalyticsPanel'
import { BottomInsightsPanel } from '@/components/BottomInsightsPanel'
import { TimeSlider } from '@/components/TimeSlider'
import { LocationAnalysisPanel } from '@/components/LocationAnalysisPanel'
import { LoadingScreen } from '@/components/LoadingScreen'

const InteractiveMap = dynamic(
  () => import('@/components/InteractiveMap'),
  { ssr: false }
)

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<string>('2020-01-15')
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [aqiLayer, setAqiLayer] = useState(true)
  
  // Demo states
  const [demoTrajectory, setDemoTrajectory] = useState(false)
  const [demoUncertainty, setDemoUncertainty] = useState(false)
  const [demoSplitView, setDemoSplitView] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 2000)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return <LoadingScreen />
  }

  return (
    <div className="w-full h-screen bg-mission-bg text-white overflow-hidden flex flex-col font-sans">
      {/* Top Navigation */}
      <TopNavigation selectedDate={selectedDate} />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden gap-0 relative">
        {/* Left Control Panel */}
        <LeftControlPanel
          onLocationSelect={setSelectedLocation}
          aqiLayer={aqiLayer}
          onAqiLayerToggle={setAqiLayer}
          demoTrajectory={demoTrajectory}
          onDemoTrajectoryToggle={setDemoTrajectory}
          demoUncertainty={demoUncertainty}
          onDemoUncertaintyToggle={setDemoUncertainty}
          demoSplitView={demoSplitView}
          onDemoSplitViewToggle={setDemoSplitView}
        />

        {/* Central Interactive Map */}
        <div className={`flex-1 relative min-h-0 bg-[#0B0F14] flex ${demoSplitView ? 'flex-row' : ''}`}>
          <div className="flex-1 relative">
            {demoSplitView && <div className="absolute top-4 left-4 z-[400] bg-black/60 px-3 py-1 rounded text-xs font-semibold tracking-wider border border-white/10">SURFACE AQI</div>}
            <InteractiveMap 
              selectedDate={selectedDate}
              selectedLocation={selectedLocation}
              aqiLayer={aqiLayer}
              onLocationClick={setSelectedLocation}
              demoTrajectory={demoTrajectory}
              demoUncertainty={demoUncertainty}
              mapId="main-map"
            />
          </div>

          {demoSplitView && (
            <div className="flex-1 relative border-l border-white/10">
              <div className="absolute top-4 left-4 z-[400] bg-black/60 px-3 py-1 rounded text-xs font-semibold tracking-wider border border-white/10 text-purple-400">HCHO ANOMALY (FIRES)</div>
              <InteractiveMap 
                selectedDate={selectedDate}
                selectedLocation={selectedLocation}
                aqiLayer={false}
                onLocationClick={setSelectedLocation}
                demoTrajectory={false}
                demoUncertainty={false}
                mapId="hcho-map"
              />
            </div>
          )}
          
          {/* Time Slider Overlay */}
          <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 w-11/12 max-w-2xl z-[1000]">
            <TimeSlider selectedDate={selectedDate} onDateChange={setSelectedDate} />
          </div>

          {/* Location Analysis Panel */}
          {selectedLocation && (
            <LocationAnalysisPanel
              location={selectedLocation}
              date={selectedDate}
              onClose={() => setSelectedLocation(null)}
            />
          )}
        </div>

        {/* Right Analytics Panel */}
        <RightAnalyticsPanel 
          selectedDate={selectedDate}
          aqiLayer={aqiLayer}
          onAqiLayerToggle={setAqiLayer}
        />
      </div>

      {/* Bottom Insights Panel */}
      <BottomInsightsPanel selectedDate={selectedDate} />
    </div>
  )
}
