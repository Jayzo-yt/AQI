'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

interface TopNavigationProps {
  selectedDate?: string;
}

export function TopNavigation({ selectedDate }: TopNavigationProps) {
  return (
    <motion.div
      className="relative z-50 w-full h-[72px] bg-mission-panel/80 backdrop-blur-[16px] border-b border-white/5 px-8 flex items-center justify-between shadow-panel"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div className="flex items-center gap-4">
        <h1 className="text-[17px] font-semibold tracking-[0.2em] text-white drop-shadow-[0_0_15px_rgba(46,168,255,0.4)]">
          ISRO <span className="font-medium text-white/70">AQI MONITORING SYSTEM</span>
        </h1>
      </div>

      <div className="flex items-center gap-6">
        <Link
          href="/endpoints"
          className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-200 transition-colors hover:bg-white/10 hover:text-white"
        >
          API Console
        </Link>
        <div className="flex flex-col text-right text-[11px] uppercase tracking-wider text-slate-400">
          <span className="font-medium text-slate-500 mb-0.5">Mission Date</span>
          <span className="font-medium text-mission-accent drop-shadow-[0_0_8px_rgba(46,168,255,0.3)]">{selectedDate || 'N/A'}</span>
        </div>
      </div>
    </motion.div>
  )
}
