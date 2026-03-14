'use client'
import { useEffect, useState } from 'react'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'

interface Deal {
  id: number
  max_price: number
  min_price: number
  final_price: number | null
  agreement: boolean
  contract_hash: string | null
  created_at: string
}

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    API.get('/deals')
      .then(r => setDeals(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col flex-1">
      <Topbar title="📋 Deal History" />
      <main className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="text-zinc-500 text-sm">Loading deals…</div>
        ) : deals.length === 0 ? (
          <div className="bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-10 text-center text-zinc-500">
            No deals yet. Start a negotiation from the Buyer or Seller page.
          </div>
        ) : (
          <div className="bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#2a2a45]">
                  {['#', 'Max Price', 'Min Price', 'Final Price', 'Status', 'Contract Hash', 'Date'].map(h => (
                    <th key={h} className="text-left py-3 px-4 text-zinc-500 font-medium text-xs uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deals.map((d) => (
                  <tr key={d.id} className="border-b border-[#1e1e35] hover:bg-white/[0.02]">
                    <td className="py-3 px-4 text-zinc-500">{d.id}</td>
                    <td className="py-3 px-4 text-blue-400 font-semibold">${d.max_price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-pink-400 font-semibold">${d.min_price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-white font-semibold">
                      {d.final_price != null ? `$${d.final_price.toFixed(2)}` : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${d.agreement ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                        {d.agreement ? '✅ Deal' : '❌ No Deal'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-violet-400 font-mono text-xs">
                      {d.contract_hash ? `${d.contract_hash.slice(0, 16)}…` : '—'}
                    </td>
                    <td className="py-3 px-4 text-zinc-500 text-xs">
                      {new Date(d.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
