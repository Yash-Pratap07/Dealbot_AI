'use client'
import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Topbar from '@/components/Topbar'
import NegotiationPanel from '@/components/NegotiationPanel'
import ContractFlow, { DealResult } from '@/components/ContractFlow'
import type { Strategy } from '@/lib/websocket'

const STRATEGIES: { label: string; value: Strategy; icon: string; desc: string }[] = [
  { label: 'Aggressive', value: 'aggressive', icon: '🔥', desc: '4 rounds, fast close' },
  { label: 'Balanced',   value: 'balanced',   icon: '⚖️', desc: '6 rounds, steady'    },
  { label: 'Conservative', value: 'conservative', icon: '🐢', desc: '8 rounds, cautious' },
]

export default function BuyerPage() {
  const searchParams                    = useSearchParams()
  const [deal, setDeal]                 = useState<DealResult | null>(null)
  const [strategy, setStrategy]         = useState<Strategy>('balanced')
  const [initProduct, setInitProduct]   = useState<string | undefined>(undefined)
  const [initMax,     setInitMax]       = useState<number | undefined>(undefined)
  const [initMin,     setInitMin]       = useState<number | undefined>(undefined)

  useEffect(() => {
    const p = searchParams.get('product')
    const mx = searchParams.get('max')
    const mn = searchParams.get('min')
    if (p)  setInitProduct(decodeURIComponent(p))
    if (mx) setInitMax(parseFloat(mx))
    if (mn) setInitMin(parseFloat(mn))
  }, [searchParams])

  const handleDeal = (
    finalPrice: number,
    agreement: boolean,
    contractHash: string,
    rounds: { round: number; buyer: number; seller: number }[]
  ) => {
    setDeal({ finalPrice, agreement, contractHash, rounds })
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Topbar title="Buyer Dashboard" />

      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-[220px_1fr_300px] gap-0 min-h-full">

          {/* ── Left Panel ───────────────────────────────── */}
          <aside className="border-r border-gray-800 bg-gray-950 p-5 flex flex-col gap-6">
            <div>
              <p className="text-xs text-zinc-600 uppercase tracking-wider mb-3">Quick Stats</p>
              <div className="space-y-3">
                <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <p className="text-xs text-zinc-500">Active Role</p>
                  <p className="text-blue-400 font-bold mt-0.5">🔵 Buyer</p>
                </div>
                <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <p className="text-xs text-zinc-500">Strategy</p>
                  <p className="text-white font-semibold mt-0.5">Linear Convergence</p>
                </div>
                <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <p className="text-xs text-zinc-500">Last Deal</p>
                  <p className={`font-semibold mt-0.5 ${deal ? 'text-green-400' : 'text-zinc-600'}`}>
                    {deal ? `₹${deal.finalPrice.toFixed(2)}` : '—'}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <p className="text-xs text-zinc-600 uppercase tracking-wider mb-3">Strategy Controls</p>
              <div className="space-y-2">
                {STRATEGIES.map((s) => (
                  <button key={s.value}
                    onClick={() => setStrategy(s.value)}
                    className={`w-full text-left text-sm px-3 py-2 rounded-lg border transition ${
                      strategy === s.value
                        ? 'border-violet-500 bg-violet-950/40 text-white'
                        : 'border-gray-800 text-zinc-400 hover:border-violet-500/50 hover:text-white'
                    }`}>
                    <span className="mr-1.5">{s.icon}</span>{s.label}
                    <span className="block text-[10px] text-zinc-500 mt-0.5">{s.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-zinc-600 uppercase tracking-wider mb-3">Blockchain Layer</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-950/30 border border-green-800/30">
                  <span className="text-green-400 text-base">🔍</span>
                  <div>
                    <p className="text-xs font-semibold text-green-400">Transparent</p>
                    <p className="text-[10px] text-zinc-500">All deals visible on-chain</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-950/30 border border-blue-800/30">
                  <span className="text-blue-400 text-base">🔒</span>
                  <div>
                    <p className="text-xs font-semibold text-blue-400">Tamper-Proof</p>
                    <p className="text-[10px] text-zinc-500">History is immutable</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-violet-950/30 border border-violet-800/30">
                  <span className="text-violet-400 text-base">⚡</span>
                  <div>
                    <p className="text-xs font-semibold text-violet-400">Automated Payment</p>
                    <p className="text-[10px] text-zinc-500">WUSD transfers on deal</p>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* ── Main Panel ───────────────────────────────── */}
          <main className="overflow-y-auto p-6">
            <NegotiationPanel
              role="buyer"
              strategy={strategy}
              initialProduct={initProduct}
              initialMaxPrice={initMax}
              initialMinPrice={initMin}
              onDeal={handleDeal}
              onReset={() => setDeal(null)}
            />
          </main>

          {/* ── Right Panel ──────────────────────────────── */}
          <aside className="border-l border-gray-800 bg-gray-950 p-5 overflow-y-auto">
            <ContractFlow deal={deal} />
          </aside>

        </div>
      </div>
    </div>
  )
}
