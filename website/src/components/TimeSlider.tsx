'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Play, Pause, ChevronLeft, ChevronRight, ChevronUp, ChevronDown } from 'lucide-react'
import { API_BASE_URL } from '@/lib/api'

interface TimeSliderProps {
  selectedDate: string
  onDateChange: (date: string) => void
}

export function TimeSlider({ selectedDate, onDateChange }: TimeSliderProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isMinimized, setIsMinimized] = useState(true)

  useEffect(() => {
    const fetchDates = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/available-dates`)
        const data = await response.json()
        setAvailableDates(data.available_dates || [])
        const index = data.available_dates?.indexOf(selectedDate) ?? 0
        setCurrentIndex(Math.max(0, index))
      } catch (error) {
        console.error('Error fetching dates:', error)
      }
    }

    fetchDates()
  }, [])

  useEffect(() => {
    if (availableDates.length === 0) return
    const index = availableDates.indexOf(selectedDate)
    if (index !== -1) {
      setCurrentIndex(index)
    }
  }, [selectedDate, availableDates])

  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= availableDates.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 500)

    return () => clearInterval(interval)
  }, [isPlaying, availableDates.length])

  useEffect(() => {
    if (availableDates[currentIndex]) {
      onDateChange(availableDates[currentIndex])
    }
  }, [currentIndex, availableDates, onDateChange])

  const handlePrevious = () => {
    setCurrentIndex((prev) => Math.max(0, prev - 1))
  }

  const handleNext = () => {
    setCurrentIndex((prev) => Math.min(availableDates.length - 1, prev + 1))
  }

  const handleSliderChange = (index: number) => {
    setCurrentIndex(index)
    setIsPlaying(false)
  }

  const progress = availableDates.length > 0 ? (currentIndex / (availableDates.length - 1)) * 100 : 0

  return (
    <motion.div
      className="bg-mission-panel/95 backdrop-blur-[16px] border border-white/5 shadow-panel rounded-2xl p-5 w-full mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.5, ease: "easeOut" }}
    >
      <div className="space-y-4">
        {/* Date Display */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1.5 hover:bg-mission-secondary rounded-md border border-transparent hover:border-white/5 transition-all"
            >
              {isMinimized ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
            </button>
            <div className="text-[11px] font-semibold tracking-[0.15em] text-slate-300 drop-shadow-sm">DATE SELECTION</div>
          </div>
          <div className="flex items-center gap-2">
            <input 
              type="date" 
              value={selectedDate}
              onChange={(e) => {
                if (e.target.value) {
                  onDateChange(e.target.value);
                  const idx = availableDates.indexOf(e.target.value);
                  if (idx !== -1) setCurrentIndex(idx);
                }
              }}
              className="bg-mission-secondary/80 text-slate-200 border border-white/5 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-mission-accent/50 focus:ring-1 focus:ring-mission-accent/30 transition-all cursor-pointer"
            />
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Slider */}
            <div className="flex items-center gap-4">
              {/* Play Controls */}
              <div className="flex items-center gap-1.5">
                <button
                  onClick={handlePrevious}
                  disabled={currentIndex === 0}
                  className="p-1.5 hover:bg-mission-secondary rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-all border border-transparent hover:border-white/5"
                >
                  <ChevronLeft size={16} className="text-slate-300" />
                </button>

                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-1.5 hover:bg-mission-secondary rounded-md transition-all border border-transparent hover:border-white/5"
                >
                  {isPlaying ? (
                    <Pause size={16} className="text-mission-accent drop-shadow-sm" />
                  ) : (
                    <Play size={16} className="text-mission-accent drop-shadow-sm" />
                  )}
                </button>

                <button
                  onClick={handleNext}
                  disabled={currentIndex === availableDates.length - 1}
                  className="p-1.5 hover:bg-mission-secondary rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-all border border-transparent hover:border-white/5"
                >
                  <ChevronRight size={16} className="text-slate-300" />
                </button>
              </div>

              {/* Slider Track */}
              <div className="flex-1 px-2">
                <input
                  type="range"
                  min="0"
                  max={Math.max(availableDates.length - 1, 0)}
                  value={currentIndex}
                  onChange={(e) => handleSliderChange(parseInt(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer slider shadow-[inset_0_1px_3px_rgba(0,0,0,0.3)]"
                  style={{
                    background: `linear-gradient(to right, #2EA8FF ${progress}%, rgba(255,255,255,0.08) ${progress}%)`,
                  }}
                />
              </div>
            </div>

            {/* Progress Info */}
            <div className="flex items-center justify-between text-[10px] font-medium text-slate-500 pt-1">
              <span className="text-slate-400">{selectedDate}</span>
              <span>{currentIndex + 1} of {availableDates.length || 1}</span>
              <span className={isPlaying ? "text-mission-accent" : ""}>{isPlaying ? 'Playing' : 'Paused'}</span>
            </div>
          </>
        )}
      </div>

      <style jsx>{`
        input[type='range']::-webkit-slider-thumb {
          appearance: none;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: #2EA8FF;
          cursor: pointer;
          box-shadow: 0 0 10px rgba(46, 168, 255, 0.4), 0 0 0 3px rgba(46, 168, 255, 0.15);
          transition: transform 0.1s;
        }
        input[type='range']::-webkit-slider-thumb:hover {
          transform: scale(1.1);
        }

        input[type='range']::-moz-range-thumb {
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: #2EA8FF;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 10px rgba(46, 168, 255, 0.4), 0 0 0 3px rgba(46, 168, 255, 0.15);
          transition: transform 0.1s;
        }
        input[type='range']::-moz-range-thumb:hover {
          transform: scale(1.1);
        }
      `}</style>
    </motion.div>
  )
}
