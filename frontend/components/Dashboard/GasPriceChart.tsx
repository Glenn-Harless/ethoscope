'use client'

import { useMemo, useState } from 'react'
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Fuel, TrendingUp, Clock } from 'lucide-react'
import { useMetricsStore } from '@/store/metricsStore'

export default function GasPriceChart() {
  const { gasHistory, currentGasPrice, predictions } = useMetricsStore()
  const [showPrediction, setShowPrediction] = useState(true)

  const chartData = useMemo(() => {
    const historicalData = gasHistory.map((metric) => ({
      time: new Date(metric.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      actual: metric.gas_price_gwei,
      base: metric.base_fee_gwei,
      priority: metric.priority_fee_gwei,
    }))

    // Add prediction point if available
    if (showPrediction && predictions.gas_price) {
      const futureTime = new Date(Date.now() + 15 * 60 * 1000).toLocaleTimeString(
        'en-US',
        { hour: '2-digit', minute: '2-digit' }
      )

      historicalData.push({
        time: futureTime,
        actual: undefined as any,
        base: undefined as any,
        priority: undefined as any,
        predicted: predictions.gas_price,
        lower: predictions.confidence_lower || undefined,
        upper: predictions.confidence_upper || undefined,
      } as any)
    }

    return historicalData
  }, [gasHistory, predictions, showPrediction])

  const formatGwei = (value: number) => `${value?.toFixed(1)} Gwei`

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <p
              key={index}
              className="text-sm"
              style={{ color: entry.color }}
            >
              {entry.name}: {formatGwei(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Fuel className="w-6 h-6 text-eth-blue" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Gas Price Tracker
          </h2>
        </div>

        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showPrediction}
            onChange={(e) => setShowPrediction(e.target.checked)}
            className="w-4 h-4 text-eth-blue rounded focus:ring-eth-blue"
          />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Show 15-min prediction
          </span>
        </label>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorBase" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorPriority" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorPrediction" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="time"
            className="text-xs"
            tick={{ fill: '#6B7280' }}
          />
          <YAxis
            tickFormatter={(value) => `${value}`}
            className="text-xs"
            tick={{ fill: '#6B7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          <Area
            type="monotone"
            dataKey="base"
            stroke="#3B82F6"
            fillOpacity={1}
            fill="url(#colorBase)"
            strokeWidth={2}
            name="Base Fee"
          />

          <Area
            type="monotone"
            dataKey="priority"
            stroke="#8B5CF6"
            fillOpacity={1}
            fill="url(#colorPriority)"
            strokeWidth={2}
            name="Priority Fee"
          />

          {showPrediction && predictions.gas_price && (
            <>
              <Area
                type="monotone"
                dataKey="upper"
                stroke="transparent"
                fillOpacity={1}
                fill="url(#colorPrediction)"
                name="Upper Bound"
              />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#10B981"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#10B981', r: 4 }}
                name="Predicted"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="transparent"
                fillOpacity={1}
                fill="url(#colorPrediction)"
                name="Lower Bound"
              />
            </>
          )}
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Current
            </span>
            <Fuel className="w-4 h-4 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {currentGasPrice.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Gwei</p>
        </div>

        {predictions.gas_price && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                15-min Prediction
              </span>
              <TrendingUp className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {predictions.gas_price.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              ±{((predictions.confidence_upper! - predictions.confidence_lower!) / 2).toFixed(1)} Gwei
            </p>
          </div>
        )}

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Congestion
            </span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
            {predictions.congestion_level || 'Normal'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Network status
          </p>
        </div>
      </div>
    </div>
  )
}
