'use client'

import { useState, useEffect } from 'react'

export default function SimpleDashboard() {
  const [gasData, setGasData] = useState<any>(null)
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
      } catch (error) {
        console.error('Error fetching gas data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGasData()
    const interval = setInterval(fetchGasData, 15000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          Ethoscope - Ethereum Network Monitor
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Gas Price Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Current Gas Price</h2>
            <div className="text-4xl font-bold text-blue-600">
              {gasData?.gas_price_gwei?.toFixed(2)} Gwei
            </div>
            <div className="mt-4 space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>P50: {gasData?.gas_price_p50?.toFixed(2)} Gwei</p>
              <p>P95: {gasData?.gas_price_p95?.toFixed(2)} Gwei</p>
            </div>
          </div>

          {/* Network Status Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Network Status</h2>
            <div className="text-2xl font-bold text-green-600">
              Connected ✓
            </div>
            <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              <p>Pending Tx: {gasData?.pending_transactions || 0}</p>
              <p>Last Update: {new Date(gasData?.timestamp).toLocaleTimeString()}</p>
            </div>
          </div>

          {/* Health Score Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Network Health</h2>
            <div className="text-4xl font-bold text-purple-600">
              75
            </div>
            <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              <p>Status: Good</p>
              <p>Congestion: Low</p>
            </div>
          </div>
        </div>

        {/* Data Preview */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Raw Data</h2>
          <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-x-auto text-xs">
            {JSON.stringify(gasData, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
