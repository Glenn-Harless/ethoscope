'use client'

import { Activity, Info } from 'lucide-react'
import { useMetricsStore } from '@/store/metricsStore'

export default function Header() {
  const isConnected = useMetricsStore((state) => state.isConnected)

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-8 h-8 text-eth-blue" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Ethoscope
              </h1>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Ethereum Network Health Monitor
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Info className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
