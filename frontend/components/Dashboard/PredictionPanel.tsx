'use client'

import { Brain, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useMetricsStore } from '@/store/metricsStore'
import { motion } from 'framer-motion'

export default function PredictionPanel() {
  const { predictions, currentGasPrice } = useMetricsStore()

  const priceTrend = predictions.gas_price
    ? predictions.gas_price > currentGasPrice
      ? 'up'
      : predictions.gas_price < currentGasPrice
      ? 'down'
      : 'stable'
    : 'stable'

  const trendIcon = {
    up: <TrendingUp className="w-5 h-5 text-red-500" />,
    down: <TrendingDown className="w-5 h-5 text-green-500" />,
    stable: <Minus className="w-5 h-5 text-gray-500" />,
  }

  const trendText = {
    up: 'Expected to increase',
    down: 'Expected to decrease',
    stable: 'Expected to remain stable',
  }

  const congestionColor = {
    low: 'text-green-500',
    normal: 'text-blue-500',
    high: 'text-yellow-500',
    severe: 'text-red-500',
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex items-center space-x-3 mb-6">
        <Brain className="w-6 h-6 text-purple-500" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          ML Predictions
        </h2>
      </div>

      <div className="space-y-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              15-min Gas Price
            </span>
            {trendIcon[priceTrend]}
          </div>
          {predictions.gas_price ? (
            <>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {predictions.gas_price.toFixed(1)} Gwei
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {trendText[priceTrend]}
              </p>
              {predictions.confidence_lower && predictions.confidence_upper && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Confidence Range
                  </p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {predictions.confidence_lower.toFixed(1)}
                    </span>
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-400 to-blue-400"
                        style={{
                          width: '60%',
                          marginLeft: '20%',
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {predictions.confidence_upper.toFixed(1)}
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-24" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32 mt-2" />
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Network Congestion
            </span>
          </div>
          {predictions.congestion_level ? (
            <>
              <p
                className={`text-xl font-bold capitalize ${
                  congestionColor[
                    predictions.congestion_level.toLowerCase() as keyof typeof congestionColor
                  ] || 'text-gray-500'
                }`}
              >
                {predictions.congestion_level}
              </p>
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>Low</span>
                  <span>High</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      predictions.congestion_level.toLowerCase() === 'low'
                        ? 'bg-green-500 w-1/4'
                        : predictions.congestion_level.toLowerCase() === 'normal'
                        ? 'bg-blue-500 w-1/2'
                        : predictions.congestion_level.toLowerCase() === 'high'
                        ? 'bg-yellow-500 w-3/4'
                        : 'bg-red-500 w-full'
                    }`}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20" />
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded w-full mt-3" />
            </div>
          )}
        </motion.div>

        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Predictions updated every 30 seconds
          </p>
        </div>
      </div>
    </div>
  )
}
