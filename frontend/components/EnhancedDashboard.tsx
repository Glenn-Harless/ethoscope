'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'

export default function EnhancedDashboard() {
  const [gasData, setGasData] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchGasData = async () => {
      try {
        const response = await fetch('http://localhost:8003/api/v1/metrics/gas/latest', {
          headers: {
            'Authorization': 'Bearer demo-key-123'
          }
        })
        const data = await response.json()
        setGasData(data)

        // Add to history (keep last 20 points)
        setHistory(prev => {
          const timeStr = new Date(data.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          })
          const newHistory = [...prev, {
            time: timeStr,
            price: data.gas_price_gwei,
            p50: data.gas_price_p50,
            p95: data.gas_price_p95,
          }].slice(-20)
          return newHistory
        })
      } catch (error) {
        console.error('Error fetching gas data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGasData()
    const interval = setInterval(fetchGasData, 60000) // Update every 60 seconds instead of 15
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    )
  }

  const getHealthScore = () => {
    // Simple health score based on gas price
    const price = gasData?.gas_price_gwei || 0
    if (price < 1) return 90
    if (price < 2) return 75
    if (price < 5) return 60
    if (price < 10) return 40
    return 20
  }

  const healthScore = getHealthScore()
  const healthStatus = healthScore >= 80 ? 'Excellent' : healthScore >= 60 ? 'Good' : healthScore >= 40 ? 'Fair' : 'Poor'
  const healthColor = healthScore >= 80 ? 'text-green-600' : healthScore >= 60 ? 'text-blue-600' : healthScore >= 40 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Current Gas Price */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Current Gas Price</h3>
            <div className="text-3xl font-bold text-blue-600">
              {gasData?.gas_price_gwei?.toFixed(3)} Gwei
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Updated: {new Date(gasData?.timestamp).toLocaleTimeString()}
            </p>
          </div>

          {/* Health Score */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Network Health</h3>
            <div className={`text-3xl font-bold ${healthColor}`}>
              {healthScore}/100
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Status: {healthStatus}
            </p>
          </div>

          {/* P50 Gas Price */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Median Gas (P50)</h3>
            <div className="text-3xl font-bold text-purple-600">
              {gasData?.gas_price_p50?.toFixed(3)} Gwei
            </div>
            <p className="text-xs text-gray-500 mt-2">
              50th percentile
            </p>
          </div>

          {/* P95 Gas Price */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">High Gas (P95)</h3>
            <div className="text-3xl font-bold text-orange-600">
              {gasData?.gas_price_p95?.toFixed(3)} Gwei
            </div>
            <p className="text-xs text-gray-500 mt-2">
              95th percentile
            </p>
          </div>
        </div>

        {/* Chart */}
        {history.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Gas Price History</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorP95" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F97316" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="p95"
                  stroke="#F97316"
                  fillOpacity={1}
                  fill="url(#colorP95)"
                  name="P95"
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#3B82F6"
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                  strokeWidth={2}
                  name="Current"
                />
                <Line
                  type="monotone"
                  dataKey="p50"
                  stroke="#8B5CF6"
                  strokeDasharray="5 5"
                  dot={false}
                  name="P50"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Transaction Cost Estimator */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Transaction Cost Estimates</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Simple Transfer</p>
              <p className="text-lg font-bold">
                ${((gasData?.gas_price_gwei || 0) * 21000 * 2400 / 1e9).toFixed(2)} USD
              </p>
              <p className="text-xs text-gray-500">21,000 gas @ $2,400/ETH</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Token Swap</p>
              <p className="text-lg font-bold">
                ${((gasData?.gas_price_gwei || 0) * 150000 * 2400 / 1e9).toFixed(2)} USD
              </p>
              <p className="text-xs text-gray-500">150,000 gas @ $2,400/ETH</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">NFT Mint</p>
              <p className="text-lg font-bold">
                ${((gasData?.gas_price_gwei || 0) * 200000 * 2400 / 1e9).toFixed(2)} USD
              </p>
              <p className="text-xs text-gray-500">200,000 gas @ $2,400/ETH</p>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Network Stats */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Network Statistics</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Pending Transactions</span>
                <span className="font-semibold">{gasData?.pending_transactions || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Gas Price Trend</span>
                <span className="font-semibold">
                  {history.length > 1 && history[history.length - 1].price > history[history.length - 2].price ? '📈 Rising' : '📉 Falling'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Data Points Collected</span>
                <span className="font-semibold">{history.length}/20</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Update Frequency</span>
                <span className="font-semibold">Every 60 seconds</span>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Recommendations</h2>
            <div className="space-y-3">
              {gasData?.gas_price_gwei < 1 ? (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-700 font-medium">✅ Excellent Conditions</p>
                  <p className="text-green-600 text-sm mt-1">Gas prices are very low - perfect time for transactions!</p>
                </div>
              ) : gasData?.gas_price_gwei < 2 ? (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-blue-700 font-medium">👍 Good Conditions</p>
                  <p className="text-blue-600 text-sm mt-1">Normal gas prices - safe to proceed with transactions.</p>
                </div>
              ) : gasData?.gas_price_gwei < 5 ? (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-700 font-medium">⚠️ Moderate Congestion</p>
                  <p className="text-yellow-600 text-sm mt-1">Consider waiting if transaction is not urgent.</p>
                </div>
              ) : (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 font-medium">🚨 High Congestion</p>
                  <p className="text-red-600 text-sm mt-1">Use L2 solutions or wait for better conditions.</p>
                </div>
              )}

              <div className="pt-2 border-t">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Median gas (P50):</span>
                  <span className="font-medium">{gasData?.gas_price_p50?.toFixed(3)} Gwei</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-600">High gas (P95):</span>
                  <span className="font-medium">{gasData?.gas_price_p95?.toFixed(3)} Gwei</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
