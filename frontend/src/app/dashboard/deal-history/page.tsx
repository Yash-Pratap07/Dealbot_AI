'use client'
import { useEffect, useState } from 'react'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency } from '@/context/CurrencyContext'

interface Deal {
  id: number
  product?: string
  max_price: number; min_price: number; final_price: number | null
  agreement: boolean; contract_hash: string | null; created_at: string
}

type Filter = 'all' | 'agreed' | 'no-deal'

export default function DealHistoryPage() {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<Filter>('all')
  const { currSymbol } = useCurrency()

  useEffect(() => {
    API.get('/deals')
      .then(r => setDeals(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = deals.filter(d =>
    filter === 'all'     ? true :
    filter === 'agreed'  ? d.agreement :
    !d.agreement
  )

  const agreed     = deals.filter(d => d.agreement)
  const totalValue = agreed.reduce((sum, d) => sum + (d.final_price ?? 0), 0)
  const avgPrice   = agreed.length ? totalValue / agreed.length : 0
  const successRate = deals.length ? Math.round((agreed.length / deals.length) * 100) : 0

  const exportCSV = () => {
    const header = 'ID,Max Price,Min Price,Final Price,Status,Contract Hash,Date'
    const rows = filtered.map(d =>
      `${d.id},${d.max_price},${d.min_price},${d.final_price ?? ''},${d.agreement ? 'Agreed' : 'No Deal'},${d.contract_hash ?? ''},${d.created_at}`
    )
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = 'deal-history.csv'; a.click()
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="📋 Deal History" />
      <main className="flex-1 overflow-y-auto p-6 space-y-5">

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: '📊 Total Deals',  value: deals.length,      color: 'text-white'        },
            { label: '✅ Success Rate', value: `${successRate}%`, color: 'text-green-400'     },
            { label: '💰 Avg Price',    value: `${currSymbol}${avgPrice.toFixed(0)}`, color: 'text-blue-400' },
            { label: '💵 Total Value',  value: `${currSymbol}${totalValue.toFixed(0)}`, color: 'text-violet-400' },
          ].map(s => (
            <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs">{s.label}</p>
              <p className={`font-bold text-xl mt-1 ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {(['all', 'agreed', 'no-deal'] as Filter[]).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition capitalize ${
                  filter === f
                    ? 'border-violet-500 bg-violet-900/30 text-violet-300'
                    : 'border-gray-700 text-zinc-400 hover:text-white'
                }`}>
                {f === 'all'     ? `All (${deals.length})` :
                 f === 'agreed'  ? `✅ Agreed (${agreed.length})` :
                 `❌ No Deal (${deals.length - agreed.length})`}
              </button>
            ))}
          </div>
          <button onClick={exportCSV}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-gray-600 rounded-lg text-sm transition">
            ⬇ Export CSV
          </button>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-zinc-500 text-sm py-8 text-center">Loading deal history…</div>
        ) : filtered.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-14 text-center">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-zinc-400">
              {deals.length === 0 ? 'No deals yet. Start a negotiation to see history here.' : 'No deals match this filter.'}
            </p>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {['#', 'Product', 'Max Price', 'Min Price', 'Final Price', 'Status', 'Contract Hash', 'Date', ''].map(h => (
                    <th key={h} className="text-left py-3 px-4 text-zinc-500 font-medium text-xs uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(d => (
                  <tr key={d.id} className="border-b border-gray-800/50 hover:bg-white/2 transition">
                    <td className="py-3 px-4 text-zinc-500 font-mono text-xs">#{d.id}</td>
                    <td className="py-3 px-4 text-white text-sm font-medium">{d.product || 'item'}</td>
                    <td className="py-3 px-4 text-blue-400 font-semibold">{currSymbol}{d.max_price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-pink-400 font-semibold">{currSymbol}{d.min_price.toFixed(2)}</td>
                    <td className="py-3 px-4">
                      {d.final_price != null
                        ? <span className="text-white font-semibold">{currSymbol}{d.final_price.toFixed(2)}</span>
                        : <span className="text-zinc-600">—</span>}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        d.agreement ? 'bg-green-900/50 text-green-400' : 'bg-red-900/30 text-red-400'
                      }`}>
                        {d.agreement ? '✅ Agreed' : '❌ No Deal'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {d.contract_hash
                        ? <span className="font-mono text-xs text-violet-400">{d.contract_hash.slice(0, 14)}…</span>
                        : <span className="text-zinc-700 text-xs">—</span>}
                    </td>
                    <td className="py-3 px-4 text-zinc-500 text-xs">
                      {new Date(d.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      {d.contract_hash && (
                        <button
                          onClick={() => navigator.clipboard.writeText(d.contract_hash!)}
                          className="text-xs text-violet-400 hover:text-violet-300 transition">
                          📋 Copy Hash
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Timeline hint */}
        {filtered.length > 0 && (
          <div className="flex items-center gap-3 px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl">
            <span className="text-xl">📈</span>
            <div>
              <p className="text-white text-sm font-semibold">
                {agreed.length} successful deal{agreed.length !== 1 ? 's' : ''} worth {currSymbol}{totalValue.toFixed(2)} total
              </p>
              <p className="text-zinc-500 text-xs mt-0.5">
                {successRate}% success rate · {deals.length} total negotiations
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
