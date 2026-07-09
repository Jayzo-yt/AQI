'use client'

import { motion } from 'framer-motion'

export function LoadingScreen() {
  return (
    <div className="w-full h-screen bg-dark-950 flex flex-col items-center justify-center gap-6">
      <div className="relative w-24 h-24">
        <motion.div
          className="absolute inset-0 border-2 border-transparent border-t-white rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        />
      </div>
      
      <motion.div
        className="text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <h1 className="text-2xl font-light tracking-wider">Initializing Earth Observation System</h1>
        <p className="text-dark-300 mt-2 text-sm">Loading satellite data and AI models...</p>
      </motion.div>
    </div>
  )
}
