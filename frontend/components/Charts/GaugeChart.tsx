'use client'

import { useMemo } from 'react'

interface GaugeChartProps {
  value: number
  max: number
  size?: number
}

export default function GaugeChart({ value, max, size = 200 }: GaugeChartProps) {
  const percentage = useMemo(() => (value / max) * 100, [value, max])
  const rotation = useMemo(() => (percentage * 180) / 100 - 90, [percentage])

  const color = useMemo(() => {
    if (percentage >= 80) return '#10B981' // green
    if (percentage >= 60) return '#3B82F6' // blue
    if (percentage >= 40) return '#F59E0B' // yellow
    return '#EF4444' // red
  }, [percentage])

  return (
    <div className="relative" style={{ width: size, height: size / 2 }}>
      <svg
        width={size}
        height={size / 2}
        viewBox={`0 0 ${size} ${size / 2}`}
        className="transform -rotate-180"
      >
        {/* Background arc */}
        <path
          d={`M ${size * 0.1} ${size / 2} A ${size * 0.4} ${size * 0.4} 0 0 1 ${
            size * 0.9
          } ${size / 2}`}
          fill="none"
          stroke="currentColor"
          strokeWidth={size * 0.08}
          className="text-gray-200 dark:text-gray-700"
        />

        {/* Value arc */}
        <path
          d={`M ${size * 0.1} ${size / 2} A ${size * 0.4} ${size * 0.4} 0 0 1 ${
            size * 0.9
          } ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={size * 0.08}
          strokeDasharray={`${(percentage / 100) * Math.PI * size * 0.4} ${
            Math.PI * size * 0.4
          }`}
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Needle */}
      <div
        className="absolute bottom-0 left-1/2 origin-bottom transition-transform duration-1000 ease-out"
        style={{
          width: 4,
          height: size * 0.35,
          transform: `translateX(-50%) rotate(${rotation}deg)`,
          backgroundColor: color,
        }}
      >
        <div
          className="absolute -top-2 -left-2 rounded-full"
          style={{
            width: 8,
            height: 8,
            backgroundColor: color,
          }}
        />
      </div>

      {/* Center dot */}
      <div
        className="absolute bottom-0 left-1/2 transform -translate-x-1/2 rounded-full bg-gray-800 dark:bg-gray-200"
        style={{ width: size * 0.06, height: size * 0.06 }}
      />
    </div>
  )
}
