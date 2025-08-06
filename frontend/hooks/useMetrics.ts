'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useMetricsStore } from '@/store/metricsStore'
import { useEffect } from 'react'

export function useMetrics() {
  const {
    updateHealthScore,
    updateGasMetrics,
    addGasHistory,
    updatePredictions,
    updateNetworkStats,
    setConnected,
  } = useMetricsStore()

  // Fetch latest gas metrics
  const { data: gasData, error: gasError } = useQuery({
    queryKey: ['gas-metrics'],
    queryFn: api.getLatestGasMetrics,
    refetchInterval: 15000, // Every 15 seconds
  })

  // Debug logging
  useEffect(() => {
    console.log('Gas data:', gasData)
    console.log('Gas error:', gasError)
  }, [gasData, gasError])

  // Fetch gas history - disabled for now
  const gasHistory = null // API endpoint not working yet

  // Fetch health score
  const { data: healthData } = useQuery({
    queryKey: ['health-score'],
    queryFn: api.getHealthScore,
    refetchInterval: 30000,
  })

  // Fetch predictions
  const { data: predictions } = useQuery({
    queryKey: ['predictions'],
    queryFn: api.getPredictions,
    refetchInterval: 30000,
  })

  // Fetch network stats - simplified for now
  const networkStats = null // Use gas data instead

  // Update store when data changes
  useEffect(() => {
    if (gasData) {
      setConnected(true) // Mark as connected when we get data
      updateGasMetrics({
        gas_price_gwei: gasData.gas_price_gwei,
        base_fee_gwei: gasData.base_fee_gwei || gasData.gas_price_gwei * 0.8,
        priority_fee_gwei: gasData.priority_fee_gwei || gasData.gas_price_gwei * 0.2,
      })
    }
  }, [gasData, updateGasMetrics, setConnected])

  // Create mock history from current data
  useEffect(() => {
    if (gasData) {
      // Add current data point to history
      addGasHistory({
        timestamp: gasData.timestamp || new Date().toISOString(),
        gas_price_gwei: gasData.gas_price_gwei,
        base_fee_gwei: gasData.base_fee_gwei || gasData.gas_price_gwei * 0.8,
        priority_fee_gwei: gasData.priority_fee_gwei || gasData.gas_price_gwei * 0.2,
      })
    }
  }, [gasData, addGasHistory])

  useEffect(() => {
    if (healthData) {
      updateHealthScore(healthData.overall_score || 75)
    }
  }, [healthData, updateHealthScore])

  useEffect(() => {
    if (predictions) {
      updatePredictions({
        gas_price: predictions.gas_price_15min,
        confidence_lower: predictions.confidence_lower,
        confidence_upper: predictions.confidence_upper,
        congestion_level: predictions.congestion_level || 'normal',
      })
    }
  }, [predictions, updatePredictions])

  useEffect(() => {
    if (networkStats) {
      updateNetworkStats({
        blockTime: networkStats.block_time || 12,
        tps: networkStats.transactions_per_block || 150,
        pendingTx: gasData?.pending_transactions || 0,
      })
    }
  }, [networkStats, gasData, updateNetworkStats])

  return {
    gasData,
    gasHistory,
    healthData,
    predictions,
    networkStats,
  }
}
