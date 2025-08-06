'use client'

import { useState, useEffect } from 'react'

export default function TestPage() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching gas metrics...')
        const response = await fetch('http://localhost:8003/api/v1/metrics/gas/latest', {
          headers: {
            'Authorization': 'Bearer demo-key-123'
          },
          mode: 'cors'
        })

        console.log('Response status:', response.status)

        if (!response.ok) {
          const text = await response.text()
          throw new Error(`HTTP error! status: ${response.status}, body: ${text}`)
        }

        const json = await response.json()
        console.log('Data received:', json)
        setData(json)
        setError(null)
      } catch (err: any) {
        console.error('Fetch error:', err)
        setError(err.message || 'Failed to fetch')
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Changed to 30 seconds
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <h2 className="text-xl font-semibold mb-2">Gas Metrics Test</h2>

        {loading && <p>Loading...</p>}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            Error: {error}
          </div>
        )}

        {data && (
          <div className="space-y-2">
            <p><strong>Timestamp:</strong> {data.timestamp}</p>
            <p><strong>Gas Price:</strong> {data.gas_price_gwei?.toFixed(3)} Gwei</p>
            <p><strong>P50:</strong> {data.gas_price_p50?.toFixed(3)} Gwei</p>
            <p><strong>P95:</strong> {data.gas_price_p95?.toFixed(3)} Gwei</p>
            <p><strong>Pending Tx:</strong> {data.pending_transactions}</p>
          </div>
        )}

        <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded">
          <p className="text-sm font-mono break-all">
            {JSON.stringify(data, null, 2)}
          </p>
        </div>
      </div>
    </div>
  )
}
