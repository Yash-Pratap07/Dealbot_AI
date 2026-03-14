'use client'
import { useEffect, useState } from 'react'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'

interface Deal {
  id: number
  max_price: number; min_price: number; final_price: number | null
  agreement: boolean; contract_hash: string | null; created_at: string
}

async function sha256hex(data: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(data))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

export default function BlockchainContractsPage() {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [verifying, setVerifying] = useState<number | null>(null)
  const [verifiedHashes, setVerifiedHashes] = useState<Record<number, string>>({})
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    API.get('/deals')
      .then(r => setDeals((r.data as Deal[]).filter(d => d.contract_hash)))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const copyHash = (id: number, hash: string) => {
    navigator.clipboard.writeText(hash)
    setCopiedId(id); setTimeout(() => setCopiedId(null), 1500)
  }

  const verifyHash = async (deal: Deal) => {
    if (!deal.contract_hash) return
    setVerifying(deal.id)
    try {
      const payload = JSON.stringify({
        id: deal.id, final_price: deal.final_price, agreement: deal.agreement,
      })
      const computed = await sha256hex(payload)
      setVerifiedHashes(prev => ({ ...prev, [deal.id]: computed }))
    } finally {
      setVerifying(null)
    }
  }

  const totalContracts  = deals.length
  const agreedContracts = deals.filter(d => d.agreement).length
  const totalValue      = deals.filter(d => d.agreement).reduce((s, d) => s + (d.final_price ?? 0), 0)

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="⛓️ Blockchain Contracts" />
      <main className="flex-1 overflow-y-auto p-6 space-y-5">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: '⛓️ Total Contracts', value: totalContracts,               color: 'text-white'        },
            { label: '✅ Agreed',           value: agreedContracts,             color: 'text-green-400'    },
            { label: '💰 Total Value',      value: `$${totalValue.toFixed(0)}`, color: 'text-violet-400'   },
          ].map(s => (
            <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-zinc-500 text-xs">{s.label}</p>
              <p className={`font-bold text-xl mt-1 ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Info banner */}
        <div className="flex items-start gap-3 px-4 py-3 bg-indigo-950/30 border border-indigo-700/30 rounded-xl">
          <span className="text-xl mt-0.5">ℹ️</span>
          <p className="text-zinc-400 text-sm">
            Each deal generates a SHA-256 contract hash stored on WeilChain. Click{' '}
            <span className="text-indigo-300 font-semibold">Verify Hash</span> to recompute and confirm integrity.
          </p>
        </div>

        {/* Contracts list */}
        {loading ? (
          <div className="text-zinc-500 text-sm py-8 text-center">Loading contracts…</div>
        ) : deals.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-14 text-center">
            <div className="text-4xl mb-3">⛓️</div>
            <p className="text-zinc-400">No blockchain contracts yet. Complete a negotiation to generate one.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {deals.map(d => (
              <div key={d.id}
                className={`bg-gray-900 border rounded-2xl overflow-hidden transition-all ${
                  expanded === d.id ? 'border-violet-500/40' : 'border-gray-800'
                }`}>
                {/* Contract header */}
                <div
                  className="flex items-center gap-4 p-4 cursor-pointer hover:bg-white/2 transition"
                  onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                >
                  {/* Icon */}
                  <div className="w-10 h-10 bg-indigo-900/30 border border-indigo-700/30 rounded-xl flex items-center justify-center text-xl shrink-0">📄</div>

                  {/* ID + date */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-white font-semibold text-sm">Contract #{d.id}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        d.agreement ? 'bg-green-900/40 text-green-400' : 'bg-red-900/30 text-red-400'
                      }`}>
                        {d.agreement ? '✅ AGREED' : '❌ NO DEAL'}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-violet-400 truncate">{d.contract_hash}</p>
                  </div>

                  {/* Price */}
                  <div className="text-right shrink-0">
                    {d.final_price != null
                      ? <><p className="text-white font-bold">${d.final_price.toFixed(2)}</p>
                          <p className="text-zinc-600 text-[10px]">final</p></>
                      : <p className="text-zinc-600 text-sm">—</p>}
                  </div>

                  {/* Date */}
                  <div className="text-right text-xs text-zinc-500 shrink-0 w-24">
                    {new Date(d.created_at).toLocaleDateString()}
                  </div>

                  <span className={`text-zinc-500 text-xs transition-transform shrink-0 ${expanded === d.id ? 'rotate-90' : ''}`}>▶</span>
                </div>

                {/* Expanded detail */}
                {expanded === d.id && (
                  <div className="border-t border-gray-800 p-4 space-y-4 bg-black/10">
                    {/* Full hash */}
                    <div>
                      <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Contract Hash (SHA-256)</p>
                      <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2">
                        <p className="flex-1 font-mono text-xs text-violet-300 break-all leading-relaxed">{d.contract_hash}</p>
                        <button
                          onClick={() => copyHash(d.id, d.contract_hash!)}
                          className="shrink-0 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-zinc-300 text-xs rounded-lg transition">
                          {copiedId === d.id ? '✓ Copied!' : '📋 Copy'}
                        </button>
                      </div>
                    </div>

                    {/* Deal terms */}
                    <div className="grid grid-cols-4 gap-3 text-sm">
                      {[
                        { label: 'Max Price',   value: `$${d.max_price.toFixed(2)}`,   color: 'text-blue-400'   },
                        { label: 'Min Price',   value: `$${d.min_price.toFixed(2)}`,   color: 'text-pink-400'   },
                        { label: 'Final Price', value: d.final_price != null ? `$${d.final_price.toFixed(2)}` : '—', color: 'text-white' },
                        { label: 'Status',      value: d.agreement ? 'Agreed' : 'No Deal', color: d.agreement ? 'text-green-400' : 'text-red-400' },
                      ].map(item => (
                        <div key={item.label} className="bg-gray-800 rounded-xl p-3">
                          <p className="text-zinc-500 text-xs mb-0.5">{item.label}</p>
                          <p className={`font-semibold ${item.color}`}>{item.value}</p>
                        </div>
                      ))}
                    </div>

                    {/* Verify + Explorer */}
                    <div className="flex gap-3">
                      <button
                        onClick={() => verifyHash(d)}
                        disabled={verifying === d.id}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-900/30 border border-indigo-700/30 text-indigo-300 hover:bg-indigo-900/50 rounded-lg text-sm font-semibold transition disabled:opacity-50"
                      >
                        {verifying === d.id
                          ? <><span className="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />Verifying…</>
                          : '🔐 Verify Hash'}
                      </button>
                      <button
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white rounded-lg text-sm transition"
                        onClick={() => alert('WeilChain explorer coming soon!')}>
                        ⛓️ View on Explorer
                      </button>
                    </div>

                    {/* Verification result */}
                    {verifiedHashes[d.id] && (
                      <div className="bg-indigo-950/40 border border-indigo-700/30 rounded-xl p-3">
                        <p className="text-xs text-indigo-400 font-semibold mb-1">🔐 Computed Hash:</p>
                        <p className="font-mono text-xs text-indigo-300 break-all">{verifiedHashes[d.id]}</p>
                        <p className={`text-xs mt-2 font-semibold ${
                          verifiedHashes[d.id] === d.contract_hash ? 'text-green-400' : 'text-yellow-400'
                        }`}>
                          {verifiedHashes[d.id] === d.contract_hash
                            ? '✅ Hash matches — contract integrity verified'
                            : '⚠️ Hash differs — stored hash may use different payload'}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
