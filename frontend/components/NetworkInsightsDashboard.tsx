'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  Legend,
} from 'recharts'

interface L2TVLData {
  network: string
  tvl_usd: number
  market_share_percent: number
}

interface MEVData {
  avg_mev_revenue: number
  max_mev_revenue: number
  avg_gas_utilization: number
  unique_builders: number
}

interface NetworkStats {
  transaction_count: number
  gas_used: number
  pending_transactions: number
}

export default function NetworkInsightsDashboard() {
  const [gasData, setGasData] = useState<any>(null)
  const [l2TVL, setL2TVL] = useState<L2TVLData[]>([])
  const [mevData, setMEVData] = useState<MEVData | null>(null)
  const [networkStats, setNetworkStats] = useState<NetworkStats | null>(null)
  const [ethMainnetTVL, setEthMainnetTVL] = useState<number>(40000000000) // $40B estimated
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        // Fetch gas data
        const gasResponse = await fetch('http://localhost:8003/api/v1/metrics/gas/latest', {
          headers: { 'Authorization': 'Bearer demo-key-123' }
        })
        const gas = await gasResponse.json()
        setGasData(gas)

        // Fetch L2 TVL data
        const tvlResponse = await fetch('http://localhost:8003/api/v1/metrics/l2/tvl', {
          headers: { 'Authorization': 'Bearer demo-key-123' }
        })
        if (tvlResponse.ok) {
          const tvl = await tvlResponse.json()
          setL2TVL(tvl)
        }

        // Fetch MEV metrics
        const mevResponse = await fetch('http://localhost:8003/api/v1/metrics/mev/summary', {
          headers: { 'Authorization': 'Bearer demo-key-123' }
        })
        if (mevResponse.ok) {
          const mev = await mevResponse.json()
          setMEVData(mev)
        }

        // Fetch network stats
        const statsResponse = await fetch('http://localhost:8003/api/v1/metrics/network/stats', {
          headers: { 'Authorization': 'Bearer demo-key-123' }
        })
        if (statsResponse.ok) {
          const stats = await statsResponse.json()
          setNetworkStats(stats)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAllData()
    const interval = setInterval(fetchAllData, 60000)
    return () => clearInterval(interval)
  }, [])

  // Mock data for demonstration (since endpoints might not exist yet)
  const mockL2TVL: L2TVLData[] = [
    { network: 'Base', tvl_usd: 4167644877.63, market_share_percent: 49.56 },
    { network: 'Arbitrum', tvl_usd: 2951725153.49, market_share_percent: 35.10 },
    { network: 'Polygon', tvl_usd: 1179690033.85, market_share_percent: 14.03 },
    { network: 'Scroll', tvl_usd: 110105997.98, market_share_percent: 1.31 },
  ]

  const mockMEVData: MEVData = {
    avg_mev_revenue: 0.027,
    max_mev_revenue: 0.38,
    avg_gas_utilization: 51.49,
    unique_builders: 26
  }

  // Use mock data if real data not available
  const displayL2TVL = l2TVL.length > 0 ? l2TVL : mockL2TVL
  const displayMEVData = mevData || mockMEVData

  const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444']

  const formatTVL = (value: number) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
    return `$${value.toFixed(2)}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-2xl">Loading Network Insights...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Ethereum Network Insights
          </h1>
          <p className="text-sm text-gray-500 mt-2">Comprehensive view of Ethereum L1 and L2 ecosystem</p>
        </div>
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Gas Price */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Gas Price</h3>
            <div className="text-3xl font-bold text-blue-600">
              {gasData?.gas_price_gwei?.toFixed(3)} Gwei
            </div>
            <p className="text-xs text-gray-500 mt-2">
              P50: {gasData?.gas_price_p50?.toFixed(3)} Gwei
            </p>
          </div>

          {/* Ethereum L1 TVL */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Ethereum L1 TVL</h3>
            <div className="text-3xl font-bold text-purple-600">
              {formatTVL(ethMainnetTVL)}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              DeFi, NFTs, DAOs
            </p>
          </div>

          {/* Total L2 TVL */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Total L2 TVL</h3>
            <div className="text-3xl font-bold text-green-600">
              {formatTVL(displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Across {displayL2TVL.length} L2s
            </p>
          </div>

          {/* MEV Revenue */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">MEV Revenue</h3>
            <div className="text-3xl font-bold text-orange-600">
              {displayMEVData.avg_mev_revenue.toFixed(3)} ETH
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Avg per block
            </p>
          </div>
        </div>

        {/* TVL Overview */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Total Value Locked Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Ethereum vs L2 Comparison */}
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-3">L1 vs L2 TVL Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Ethereum L1', value: ethMainnetTVL, percentage: (ethMainnetTVL / (ethMainnetTVL + displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0)) * 100).toFixed(1) },
                      { name: 'All L2s', value: displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0), percentage: (displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0) / (ethMainnetTVL + displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0)) * 100).toFixed(1) }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    <Cell fill="#8B5CF6" />
                    <Cell fill="#10B981" />
                  </Pie>
                  <Tooltip formatter={(value: number) => formatTVL(value)} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Total Ecosystem TVL:</span>
                  <span className="font-semibold">
                    {formatTVL(ethMainnetTVL + displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0))}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">L2 Adoption Rate:</span>
                  <span className="font-semibold">
                    {((displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0) / (ethMainnetTVL + displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0))) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* L2 Breakdown */}
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-3">Layer 2 TVL Breakdown</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={displayL2TVL}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="network" />
                  <YAxis tickFormatter={(value) => formatTVL(value)} />
                  <Tooltip formatter={(value: number) => formatTVL(value)} />
                  <Bar dataKey="tvl_usd" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* L2 Market Share */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">L2 Market Share</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={displayL2TVL}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.network}: ${entry.market_share_percent.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="tvl_usd"
                >
                  {displayL2TVL.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatTVL(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">MEV Activity Trends</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Avg Revenue</p>
                  <p className="text-lg font-bold">{displayMEVData.avg_mev_revenue.toFixed(4)} ETH</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Max Revenue</p>
                  <p className="text-lg font-bold">{displayMEVData.max_mev_revenue.toFixed(4)} ETH</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Builders</p>
                  <p className="text-lg font-bold">{displayMEVData.unique_builders}</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Gas Utilization</p>
                  <p className="text-lg font-bold">{displayMEVData.avg_gas_utilization.toFixed(1)}%</p>
                </div>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  MEV extraction is a key component of the Ethereum ecosystem, representing value captured by searchers and builders through arbitrage, liquidations, and sandwich attacks.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Network Health Indicators */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Network Health Indicators</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* MEV Analysis */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium mb-3">MEV Activity</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg Revenue/Block</span>
                  <span className="text-sm font-semibold">{displayMEVData.avg_mev_revenue.toFixed(4)} ETH</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Builder Diversity</span>
                  <span className="text-sm font-semibold">{displayMEVData.unique_builders} builders</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Gas Utilization</span>
                  <span className="text-sm font-semibold">{displayMEVData.avg_gas_utilization.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* L2 Adoption */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium mb-3">L2 Adoption</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total TVL</span>
                  <span className="text-sm font-semibold">
                    {formatTVL(displayL2TVL.reduce((sum, l2) => sum + l2.tvl_usd, 0))}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Leading L2</span>
                  <span className="text-sm font-semibold">
                    {displayL2TVL[0]?.network} ({displayL2TVL[0]?.market_share_percent.toFixed(1)}%)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Active L2s</span>
                  <span className="text-sm font-semibold">{displayL2TVL.length} networks</span>
                </div>
              </div>
            </div>

            {/* Gas Market */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium mb-3">Gas Market</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Current Price</span>
                  <span className="text-sm font-semibold">{gasData?.gas_price_gwei?.toFixed(3)} Gwei</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Median (P50)</span>
                  <span className="text-sm font-semibold">{gasData?.gas_price_p50?.toFixed(3)} Gwei</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">High (P95)</span>
                  <span className="text-sm font-semibold">{gasData?.gas_price_p95?.toFixed(3)} Gwei</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Key Insights</h2>
          <div className="space-y-3">
            {/* L2 Dominance */}
            {displayL2TVL[0]?.market_share_percent > 40 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-700 font-medium">🔹 L2 Market Concentration</p>
                <p className="text-blue-600 text-sm mt-1">
                  {displayL2TVL[0]?.network} dominates with {displayL2TVL[0]?.market_share_percent.toFixed(1)}% of L2 TVL
                </p>
              </div>
            )}

            {/* MEV Activity */}
            {displayMEVData.avg_mev_revenue > 0.02 && (
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-purple-700 font-medium">💎 MEV Opportunity</p>
                <p className="text-purple-600 text-sm mt-1">
                  Average MEV revenue of {displayMEVData.avg_mev_revenue.toFixed(3)} ETH per block indicates active arbitrage
                </p>
              </div>
            )}

            {/* Network Utilization */}
            {displayMEVData.avg_gas_utilization > 50 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-orange-700 font-medium">⚡ Network Activity</p>
                <p className="text-orange-600 text-sm mt-1">
                  {displayMEVData.avg_gas_utilization.toFixed(1)}% gas utilization shows moderate network demand
                </p>
              </div>
            )}

            {/* Gas Recommendations */}
            {gasData?.gas_price_gwei < 2 && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-700 font-medium">✅ Optimal Gas Conditions</p>
                <p className="text-green-600 text-sm mt-1">
                  Low gas prices at {gasData?.gas_price_gwei?.toFixed(3)} Gwei - ideal for L1 transactions
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
