'use client'

import { Clock, Activity, Layers, AlertTriangle } from 'lucide-react'
import { useMetricsStore } from '@/store/metricsStore'
import { motion } from 'framer-motion'

export default function NetworkStats() {
  const { blockTime, tps, pendingTx, alerts, networkStatus } = useMetricsStore()

  const stats = [
    {
      label: 'Block Time',
      value: blockTime ? `${blockTime.toFixed(1)}s` : '---',
      icon: <Clock className="w-5 h-5" />,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      description: 'Average time between blocks',
    },
    {
      label: 'Transactions/sec',
      value: tps ? tps.toFixed(0) : '---',
      icon: <Activity className="w-5 h-5" />,
      color: 'text-green-500',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      description: 'Current network throughput',
    },
    {
      label: 'Pending Txns',
      value: pendingTx ? pendingTx.toLocaleString() : '---',
      icon: <Layers className="w-5 h-5" />,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      description: 'Transactions waiting to be mined',
    },
    {
      label: 'Active Alerts',
      value: alerts.length.toString(),
      icon: <AlertTriangle className="w-5 h-5" />,
      color: alerts.length > 0 ? 'text-yellow-500' : 'text-gray-500',
      bgColor: alerts.length > 0
        ? 'bg-yellow-50 dark:bg-yellow-900/20'
        : 'bg-gray-50 dark:bg-gray-900/20',
      description: 'Network anomalies detected',
    },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
        Network Statistics
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`${stat.bgColor} rounded-lg p-4 relative overflow-hidden`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className={stat.color}>{stat.icon}</div>
              {stat.label === 'Active Alerts' && alerts.length > 0 && (
                <span className="absolute top-2 right-2 w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              )}
            </div>

            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
              {stat.value}
            </p>

            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {stat.label}
            </p>

            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              {stat.description}
            </p>
          </motion.div>
        ))}
      </div>

      {alerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
        >
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                Recent Alerts
              </p>
              <div className="space-y-2">
                {alerts.slice(0, 3).map((alert) => (
                  <div
                    key={alert.id}
                    className="text-sm text-yellow-700 dark:text-yellow-300 flex items-start space-x-2"
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${
                        alert.severity === 'critical'
                          ? 'bg-red-500'
                          : alert.severity === 'high'
                          ? 'bg-orange-500'
                          : alert.severity === 'medium'
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`}
                    />
                    <div>
                      <p>{alert.message}</p>
                      <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-0.5">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">
            Network Status
          </span>
          <span
            className={`font-medium capitalize ${
              networkStatus === 'excellent'
                ? 'text-green-500'
                : networkStatus === 'good'
                ? 'text-blue-500'
                : networkStatus === 'fair'
                ? 'text-yellow-500'
                : 'text-red-500'
            }`}
          >
            {networkStatus}
          </span>
        </div>
      </div>
    </div>
  )
}
