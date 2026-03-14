'use client'
import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Topbar from '@/components/Topbar'
import NegotiationPanel from '@/components/NegotiationPanel'
import ContractFlow, { DealResult } from '@/components/ContractFlow'
import type { Strategy } from '@/lib/websocket'
import type { RoundMessage } from '@/lib/websocket'

// ── Room ID ────────────────────────────────────────────────────────────────────

function genRoomId() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  return Array.from({ length: 8 }, () => chars[Math.floor(Math.random() * chars.length)])
    .join('')
    .replace(/(.{4})(.{4})/, '$1-$2')
}

// ── Strategy options ───────────────────────────────────────────────────────────

const STRATEGIES: { label: string; value: Strategy; icon: string; desc: string }[] = [
  { label: 'Aggressive',   value: 'aggressive',   icon: '🔥', desc: '4 rounds · fast close'  },
  { label: 'Balanced',     value: 'balanced',     icon: '⚖️', desc: '6 rounds · steady'      },
  { label: 'Conservative', value: 'conservative', icon: '🐢', desc: '8 rounds · cautious'    },
]

// ── Approve Deal Button ────────────────────────────────────────────────────────

function ApproveDealBanner({
  deal,
  onApprove,
  onReject,
}: {
  deal: DealResult
  onApprove: () => void
  onReject: () => void
}) {
  return (
    <div className="bg-linear-to-r from-green-900/40 to-emerald-900/40 border border-green-500/30 rounded-2xl p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            🤝 Deal Reached!
          </h3>
          <p className="text-zinc-400 text-sm mt-0.5">
            Review the terms and approve to proceed to contract generation.
          </p>
        </div>
        <div className="text-right">
          <p className="text-zinc-500 text-xs">Final Price</p>
          <p className="text-2xl font-bold text-green-300">₹{deal.finalPrice.toFixed(2)}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-black/20 rounded-xl p-3 text-center">
          <p className="text-zinc-500 text-xs">Status</p>
          <p className={`font-bold text-sm mt-0.5 ${deal.agreement ? 'text-green-400' : 'text-red-400'}`}>
            {deal.agreement ? '✅ Agreement' : '❌ No Deal'}
          </p>
        </div>
        <div className="bg-black/20 rounded-xl p-3 text-center">
          <p className="text-zinc-500 text-xs">Rounds</p>
          <p className="font-bold text-sm text-white mt-0.5">{deal.rounds.length}</p>
        </div>
        <div className="bg-black/20 rounded-xl p-3 text-center">
          <p className="text-zinc-500 text-xs">Hash</p>
          <p className="font-mono text-[10px] text-violet-400 mt-0.5 truncate">{deal.contractHash.slice(0, 12)}…</p>
        </div>
      </div>

      {/* ── APPROVE DEAL BUTTON ── */}
      <div className="flex gap-3">
        <button
          onClick={onApprove}
          className="flex-1 py-3.5 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl transition shadow-lg shadow-green-500/20 flex items-center justify-center gap-2 text-sm"
        >
          ✅ Approve Deal &amp; Generate Contract
        </button>
        <button
          onClick={onReject}
          className="px-6 py-3.5 border border-red-700/50 text-red-400 hover:bg-red-950/30 hover:text-red-300 font-semibold rounded-xl transition text-sm"
        >
          ✗ Reject
        </button>
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function NegotiationRoomPage() {
  const searchParams = useSearchParams()
  const [roomId] = useState(genRoomId)
  const [deal, setDeal] = useState<DealResult | null>(null)
  const [approved, setApproved] = useState<boolean | null>(null)
  const [strategy, setStrategy] = useState<Strategy>('balanced')
  const [role, setRole] = useState<'buyer' | 'seller'>('buyer')

  const rawProduct = searchParams.get('product')
  const rawMax     = searchParams.get('max')
  const rawMin     = searchParams.get('min')
  const initProduct = rawProduct ? decodeURIComponent(rawProduct) : undefined
  const initMax     = rawMax     ? parseFloat(rawMax)             : undefined
  const initMin     = rawMin     ? parseFloat(rawMin)             : undefined

  const handleDeal = (
    finalPrice: number,
    agreement: boolean,
    contractHash: string,
    rounds: RoundMessage[]
  ) => {
    setDeal({ finalPrice, agreement, contractHash, rounds })
    setApproved(null)
  }

  const handleApprove = () => setApproved(true)
  const handleReject  = () => { setDeal(null); setApproved(false) }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="🤝 Negotiation Room" />

      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* ── Room Header ── */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Room ID */}
            <div>
              <p className="text-zinc-500 text-xs uppercase tracking-wide">Room ID</p>
              <p className="text-white font-mono font-bold text-lg tracking-widest">{roomId}</p>
            </div>
            {/* Live dot */}
            <div className="flex items-center gap-1.5 px-3 py-1 bg-green-900/20 border border-green-700/30 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-green-400 text-xs font-semibold">LIVE</span>
            </div>
          </div>

          {/* Role selector */}
          <div className="flex items-center gap-2">
            <p className="text-zinc-500 text-xs mr-1">Role:</p>
            {(['buyer', 'seller'] as const).map(r => (
              <button key={r}
                onClick={() => { setRole(r); setDeal(null); setApproved(null) }}
                className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition capitalize ${
                  role === r
                    ? r === 'buyer' ? 'border-blue-500 bg-blue-900/30 text-blue-300'
                                    : 'border-pink-500 bg-pink-900/30 text-pink-300'
                    : 'border-gray-700 text-zinc-500 hover:text-white'
                }`}>
                {r === 'buyer' ? '🔵' : '🔴'} {r}
              </button>
            ))}
          </div>
        </div>

        {/* ── Participants ── */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { role: 'Buyer Agent',  icon: '🔵', color: 'border-blue-500/30 bg-blue-950/20', active: role === 'buyer' },
            { role: 'Seller Agent', icon: '🔴', color: 'border-pink-500/30 bg-pink-950/20', active: role === 'seller' },
          ].map(p => (
            <div key={p.role} className={`rounded-xl border p-4 flex items-center gap-3 ${p.color}`}>
              <div className="w-10 h-10 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-xl">{p.icon}</div>
              <div>
                <p className="text-white font-semibold text-sm">{p.role}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${p.active ? 'bg-green-400 animate-pulse' : 'bg-zinc-600'}`} />
                  <span className="text-xs text-zinc-500">{p.active ? 'You (active)' : 'AI Agent'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Strategy picker ── */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Negotiation Strategy</p>
          <div className="grid grid-cols-3 gap-2">
            {STRATEGIES.map(s => (
              <button key={s.value}
                onClick={() => setStrategy(s.value)}
                className={`flex flex-col items-center p-3 rounded-xl border text-sm font-semibold transition ${
                  strategy === s.value
                    ? 'bg-violet-900/30 border-violet-500/60 text-violet-300'
                    : 'border-gray-700 text-zinc-400 hover:border-gray-600 hover:text-white'
                }`}>
                <span className="text-2xl mb-1">{s.icon}</span>
                {s.label}
                <span className="text-[10px] font-normal text-zinc-500 mt-0.5">{s.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Product pre-fill info ── */}
        {initProduct && (
          <div className="px-4 py-2.5 bg-violet-900/20 border border-violet-700/30 rounded-xl flex items-center gap-3 text-sm">
            <span className="text-violet-400">🛒</span>
            <div>
              <span className="text-white font-semibold">{initProduct}</span>
              {initMax && <span className="text-zinc-400 ml-2">· Max ₹{initMax.toFixed(2)}</span>}
              {initMin && <span className="text-zinc-400 ml-1">· Min ₹{initMin.toFixed(2)}</span>}
            </div>
          </div>
        )}

        {/* ── Approve Deal Banner ── */}
        {deal && approved === null && deal.agreement && (
          <ApproveDealBanner deal={deal} onApprove={handleApprove} onReject={handleReject} />
        )}

        {approved === false && (
          <div className="px-4 py-3 bg-red-950/30 border border-red-700/30 rounded-xl text-red-400 text-sm">
            ❌ Deal rejected. Start a new negotiation below.
          </div>
        )}

        {/* ── Main grid: Negotiation + Contract ── */}
        <div className="grid grid-cols-[1fr_320px] gap-5">
          <div>
            <NegotiationPanel
              role={role}
              strategy={strategy}
              initialProduct={initProduct}
              initialMaxPrice={initMax}
              initialMinPrice={initMin}
              onDeal={handleDeal}
              onReset={() => { setDeal(null); setApproved(null) }}
            />
          </div>
          <div>
            <ContractFlow deal={approved ? deal : null} />
          </div>
        </div>
      </div>
    </div>
  )
}
