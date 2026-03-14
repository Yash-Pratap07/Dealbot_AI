'use client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'

interface LogEntry { round: number; buyer: number; seller: number }

interface Props {
  logs: LogEntry[]
  minPrice?: number
  maxPrice?: number
  finalPrice?: number
}

export default function OfferGraph({ logs, minPrice, maxPrice, finalPrice }: Props) {
  if (!logs || logs.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-zinc-600 text-sm">
        Graph will appear as rounds progress…
      </div>
    )
  }

  const yMin = minPrice != null ? minPrice * 0.9 : 'auto'
  const yMax = maxPrice != null ? maxPrice * 1.1 : 'auto'

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={logs} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="round"
          label={{ value: 'Round', position: 'insideBottom', offset: -2, fill: '#6b7280', fontSize: 11 }}
          tick={{ fill: '#6b7280', fontSize: 11 }}
        />
        <YAxis
          domain={[yMin, yMax]}
          tick={{ fill: '#6b7280', fontSize: 11 }}
          tickFormatter={(v) => `₹${v}`}
        />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
          labelStyle={{ color: '#9ca3af', fontSize: 11 }}
          formatter={(val: number | undefined) => val != null ? [`₹${val.toFixed(2)}`] : ['-']}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af', paddingTop: 8 }} />
        {finalPrice != null && (
          <ReferenceLine y={finalPrice} stroke="#00ff9d" strokeDasharray="4 4"
            label={{ value: `Deal ₹${finalPrice}`, fill: '#00ff9d', fontSize: 11 }} />
        )}
        <Line type="monotone" dataKey="buyer" stroke="#00ff9d" strokeWidth={2}
          dot={{ r: 4, fill: '#00ff9d' }} name="Buyer" />
        <Line type="monotone" dataKey="seller" stroke="#ff4d4d" strokeWidth={2}
          dot={{ r: 4, fill: '#ff4d4d' }} name="Seller" />
      </LineChart>
    </ResponsiveContainer>
  )
}
