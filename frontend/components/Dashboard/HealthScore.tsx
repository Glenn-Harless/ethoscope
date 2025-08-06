'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Activity, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import { useMetricsStore } from '@/store/metricsStore'
import GaugeChart from '../Charts/GaugeChart'

export default function HealthScore() {
  const { healthScore, networkStatus } = useMetricsStore()

  const statusConfig = useMemo(() => {
    switch (networkStatus) {
      case 'excellent':
        return {
          text: 'Excellent',
          color: 'text-green-500',
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          icon: <TrendingUp className="w-5 h-5 text-green-500" />,
          message: 'Network is operating optimally. Perfect time for transactions.',
        }
      case 'good':
        return {
          text: 'Good',
          color: 'text-blue-500',
          bgColor: 'bg-blue-50 dark:bg-blue-900/20',
          borderColor: 'border-blue-200 dark:border-blue-800',
          icon: <Activity className="w-5 h-5 text-blue-500" />,
          message: 'Network conditions are stable. Normal transaction costs.',
        }
      case 'fair':
        return {
          text: 'Fair',
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          borderColor: 'border-yellow-200 dark:border-yellow-800',
          icon: <AlertCircle className="w-5 h-5 text-yellow-500" />,
          message: 'Some congestion detected. Consider delaying non-urgent transactions.',
        }
      default:
        return {
          text: 'Poor',
          color: 'text-red-500',
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          icon: <TrendingDown className="w-5 h-5 text-red-500" />,
          message: 'High congestion. Use L2 solutions or wait for better conditions.',
        }
    }
  }, [networkStatus])

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Network Health Score
        </h2>
        <div className="flex items-center space-x-2">
          {statusConfig.icon}
          <span className={`font-semibold ${statusConfig.color}`}>
            {statusConfig.text}
          </span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
        <div className="flex-1 w-full max-w-sm">
          <GaugeChart value={healthScore} max={100} />
        </div>

        <div className="flex-1 space-y-4">
          <div className="text-center lg:text-left">
            <p className="text-5xl font-bold text-gray-900 dark:text-white">
              {healthScore}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              out of 100
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`p-4 rounded-lg border ${statusConfig.bgColor} ${statusConfig.borderColor}`}
          >
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {statusConfig.message}
            </p>
          </motion.div>

          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">Gas Price</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {healthScore > 70 ? 'Low' : healthScore > 40 ? 'Medium' : 'High'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">Block Time</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {healthScore > 60 ? 'Normal' : 'Slow'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">MEV Impact</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {healthScore > 50 ? 'Minimal' : 'Elevated'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
