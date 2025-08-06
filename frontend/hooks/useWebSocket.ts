'use client'

import { useEffect, useCallback, useRef } from 'react'
import io, { Socket } from 'socket.io-client'
import { useMetricsStore } from '@/store/metricsStore'

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null)
  const {
    setConnected,
    updateHealthScore,
    updateGasMetrics,
    addGasHistory,
    updatePredictions,
    updateNetworkStats,
    addAlert,
  } = useMetricsStore()

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8003'

    socketRef.current = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      path: '/ws/socket.io/',
    })

    const socket = socketRef.current

    socket.on('connect', () => {
      console.log('WebSocket connected')
      setConnected(true)

      // Subscribe to channels
      socket.emit('subscribe', {
        channels: ['health_score', 'gas_metrics', 'predictions', 'alerts', 'network_stats']
      })
    })

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    })

    socket.on('health_score', (data: any) => {
      updateHealthScore(data.overall_score)
    })

    socket.on('gas_metrics', (data: any) => {
      updateGasMetrics({
        gas_price_gwei: data.gas_price_gwei,
        base_fee_gwei: data.base_fee_gwei,
        priority_fee_gwei: data.priority_fee_gwei,
      })

      addGasHistory({
        timestamp: data.timestamp,
        gas_price_gwei: data.gas_price_gwei,
        base_fee_gwei: data.base_fee_gwei,
        priority_fee_gwei: data.priority_fee_gwei,
      })
    })

    socket.on('predictions', (data: any) => {
      updatePredictions({
        gas_price: data.gas_price_15min,
        confidence_lower: data.confidence_lower,
        confidence_upper: data.confidence_upper,
        congestion_level: data.congestion_level,
      })
    })

    socket.on('network_stats', (data: any) => {
      updateNetworkStats({
        blockTime: data.block_time,
        tps: data.tps,
        pendingTx: data.pending_tx_count,
      })
    })

    socket.on('alert', (data: any) => {
      addAlert({
        id: `${Date.now()}-${Math.random()}`,
        type: data.alert_type || 'anomaly',
        severity: data.severity || 'medium',
        message: data.message,
        timestamp: new Date().toISOString(),
      })
    })

    socket.on('error', (error: any) => {
      console.error('WebSocket error:', error)
    })

    socket.on('reconnect', (attemptNumber: number) => {
      console.log(`WebSocket reconnected after ${attemptNumber} attempts`)
      setConnected(true)
    })

    socket.on('reconnect_error', (error: any) => {
      console.error('WebSocket reconnection error:', error)
    })
  }, [setConnected, updateHealthScore, updateGasMetrics, addGasHistory, updatePredictions, updateNetworkStats, addAlert])

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect()
      socketRef.current = null
    }
  }, [])

  return { connect, disconnect }
}
