import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface GasMetric {
  timestamp: string
  gas_price_gwei: number
  base_fee_gwei: number
  priority_fee_gwei: number
}

export interface Prediction {
  gas_price: number | null
  confidence_lower: number | null
  confidence_upper: number | null
  congestion_level: string | null
}

export interface Alert {
  id: string
  type: 'anomaly' | 'threshold' | 'prediction'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  timestamp: string
}

interface MetricsState {
  // Connection status
  isConnected: boolean

  // Health metrics
  healthScore: number
  networkStatus: 'excellent' | 'good' | 'fair' | 'poor'

  // Gas metrics
  currentGasPrice: number
  gasHistory: GasMetric[]

  // Predictions
  predictions: Prediction

  // Network stats
  blockTime: number
  tps: number
  pendingTx: number

  // Alerts
  alerts: Alert[]

  // Actions
  setConnected: (connected: boolean) => void
  updateHealthScore: (score: number) => void
  updateGasMetrics: (metrics: Partial<GasMetric>) => void
  addGasHistory: (metric: GasMetric) => void
  updatePredictions: (predictions: Prediction) => void
  updateNetworkStats: (stats: { blockTime?: number; tps?: number; pendingTx?: number }) => void
  addAlert: (alert: Alert) => void
  clearAlerts: () => void
}

export const useMetricsStore = create<MetricsState>()(
  subscribeWithSelector((set) => ({
    // Initial state
    isConnected: false,
    healthScore: 0,
    networkStatus: 'good',
    currentGasPrice: 0,
    gasHistory: [],
    predictions: {
      gas_price: null,
      confidence_lower: null,
      confidence_upper: null,
      congestion_level: null,
    },
    blockTime: 0,
    tps: 0,
    pendingTx: 0,
    alerts: [],

    // Actions
    setConnected: (connected) => set({ isConnected: connected }),

    updateHealthScore: (score) => set((state) => {
      let status: 'excellent' | 'good' | 'fair' | 'poor' = 'good'
      if (score >= 80) status = 'excellent'
      else if (score >= 60) status = 'good'
      else if (score >= 40) status = 'fair'
      else status = 'poor'

      return { healthScore: score, networkStatus: status }
    }),

    updateGasMetrics: (metrics) => set((state) => ({
      currentGasPrice: metrics.gas_price_gwei || state.currentGasPrice,
    })),

    addGasHistory: (metric) => set((state) => ({
      gasHistory: [...state.gasHistory.slice(-99), metric], // Keep last 100
    })),

    updatePredictions: (predictions) => set({ predictions }),

    updateNetworkStats: (stats) => set((state) => ({
      blockTime: stats.blockTime ?? state.blockTime,
      tps: stats.tps ?? state.tps,
      pendingTx: stats.pendingTx ?? state.pendingTx,
    })),

    addAlert: (alert) => set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 20), // Keep last 20 alerts
    })),

    clearAlerts: () => set({ alerts: [] }),
  }))
)
