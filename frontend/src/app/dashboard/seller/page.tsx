'use client'
import { useState } from 'react'
import Topbar from '@/components/Topbar'
import NegotiationPanel from '@/components/NegotiationPanel'
import ContractFlow from '@/components/ContractFlow'
import type { DealResult } from '@/components/ContractFlow'
import type { RoundMessage } from '@/lib/websocket'

type Strategy = 'aggressive' | 'balanced' | 'conservative'

const STRATEGIES: { id: Strategy; label: string; desc: string; color: string }[] = [
  { id: 'aggressive',   label: '🔥 Aggressive',   desc: 'Hold firm, minimal concessions', color: 'border-red-500/40 bg-red-950/30 text-red-300' },
  { id: 'balanced',     label: '⚖️ Balanced',      desc: 'Fair middle ground',             color: 'border-violet-500/40 bg-violet-950/30 text-violet-300' },
  { id: 'conservative', label: '🛡️ Conservative', desc: 'Protect minimum, slow reduce',   color: 'border-blue-500/40 bg-blue-950/30 text-blue-300' },
]

export default function SellerPage() {
  const [strategy, setStrategy] = useState<Strategy>('balanced')
  const [deal, setDeal] = useState<DealResult | null>(null)

  return (
    <div className="flex flex-col flex-1">
      <Topbar title="🔴 Seller Agent — Set Your Price" />
      <main className="flex-1 overflow-y-auto p-6">
        <p className="text-zinc-500 text-sm mb-6">
          You are the <span className="text-pink-400 font-semibold">Seller</span>. Set your minimum acceptable price and let the AI agent negotiate the highest price with the Buyer Agent.
        </p>

        {/* Strategy selector */}
        <div className="mb-6">
          <h3 className="text-xs text-zinc-500 uppercase tracking-widest font-semibold mb-3">Seller Strategy</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {STRATEGIES.map(s => (
              <button
                key={s.id}
                onClick={() => setStrategy(s.id)}
                className={`rounded-xl border px-4 py-3 text-left transition-all ${
                  strategy === s.id ? s.color + ' ring-1 ring-white/10' : 'border-[#2a2a45] bg-[#1a1a2e] text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <div className="font-semibold text-sm">{s.label}</div>
                <div className="text-xs mt-1 opacity-70">{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Main negotiation panel */}
          <div className="xl:col-span-2">
            <NegotiationPanel
              role="seller"
              strategy={strategy}
              onDeal={(finalPrice, agreement, contractHash, rounds) =>
                setDeal({ finalPrice, agreement, contractHash, rounds })
              }
              onReset={() => setDeal(null)}
            />
          </div>

          {/* Right sidebar: deal info + contract */}
          <div className="space-y-4">
            {deal ? (
              <>
                <div className={`rounded-2xl border p-5 ${
                  deal.agreement ? 'bg-green-950/30 border-green-700/40' : 'bg-red-950/30 border-red-700/40'
                }`}>
                  <div className={`text-lg font-bold ${deal.agreement ? 'text-green-400' : 'text-red-400'}`}>
                    {deal.agreement ? '✅ Deal Closed' : '❌ No Deal'}
                  </div>
                  {deal.agreement && (
                    <div className="text-white font-semibold mt-1">
                      Sold at: <span className="text-green-400">${deal.finalPrice.toLocaleString('en', { minimumFractionDigits: 2 })}</span>
                    </div>
                  )}
                  <div className="text-xs text-zinc-500 mt-2">Rounds: {deal.rounds.length}</div>
                </div>

                {deal.agreement && deal.contractHash && (
                  <ContractFlow deal={deal} />
                )}
              </>
            ) : (
              <div className="rounded-2xl border border-[#2a2a45] bg-[#1a1a2e] p-5">
                <h3 className="text-sm font-semibold text-zinc-400 mb-3">💡 Seller Tips</h3>
                <ul className="text-xs text-zinc-500 space-y-2 list-disc list-inside">
                  <li>Set your <strong className="text-zinc-300">minimum price</strong> carefully — the AI won&apos;t go below it</li>
                  <li><strong className="text-zinc-300">Aggressive</strong> strategy holds firm on price with minimal concessions</li>
                  <li><strong className="text-zinc-300">Conservative</strong> slowly reduces price to close the deal</li>
                  <li>Watch the <strong className="text-zinc-300">convergence graph</strong> to see how prices meet</li>
                  <li>After a deal, review the <strong className="text-zinc-300">multi-LLM vote</strong> for fairness</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
