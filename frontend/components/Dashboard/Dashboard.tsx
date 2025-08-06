'use client'

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import HealthScore from './HealthScore'
import GasPriceChart from './GasPriceChart'
import NetworkStats from './NetworkStats'
import PredictionPanel from './PredictionPanel'
import Header from '../Layout/Header'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMetrics } from '@/hooks/useMetrics'

export default function Dashboard() {
  const { connect, disconnect } = useWebSocket()
  const { gasData, healthData } = useMetrics() // Fetch data from API

  // Disable WebSocket for now - it's causing issues
  // useEffect(() => {
  //   connect()
  //   return () => disconnect()
  // }, [connect, disconnect])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="col-span-full"
          >
            <HealthScore />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            <GasPriceChart />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <PredictionPanel />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="col-span-full"
          >
            <NetworkStats />
          </motion.div>
        </div>
      </div>
    </div>
  )
}
