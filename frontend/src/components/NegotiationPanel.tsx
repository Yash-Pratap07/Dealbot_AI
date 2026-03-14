'use client'
import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import OfferGraph from './OfferGraph'
import ModelSelector from './ModelSelector'
import {
  connectNegotiation, WSMessage, DoneMessage, RoundMessage, Strategy,
  VoteResult, VotingResult, EvaluationResult,
} from '@/lib/websocket'
import { useCurrency } from '@/context/CurrencyContext'

// ─── Local Types ──────────────────────────────────────────────────────────────

interface Props {
  role: 'buyer' | 'seller'
  strategy?: Strategy
  initialProduct?: string
  initialMaxPrice?: number
  initialMinPrice?: number
  onDeal?: (finalPrice: number, agreement: boolean, contractHash: string, rounds: RoundMessage[]) => void
  onReset?: () => void
}

const MODEL_COLORS: Record<string, string> = {
  GPT:    'bg-green-500/20 text-green-300 border-green-500/30',
  Claude: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  Gemini: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  gemini: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function VotesPanel({ votes }: { votes: VotingResult }) {
  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">🗳 Multi-LLM Voting</h3>
        <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
          votes.decision === 'ACCEPT'
            ? 'bg-green-500/20 text-green-400 border-green-500/40'
            : 'bg-red-500/20 text-red-400 border-red-500/40'
        }`}>
          {votes.accept_count}/3 → {votes.decision}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {votes.votes.map((v: VoteResult) => (
          <div key={v.model} className={`rounded-xl p-3 border ${
            v.vote === 'ACCEPT'
              ? 'bg-green-950/30 border-green-700/30'
              : 'bg-red-950/30 border-red-700/30'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${MODEL_COLORS[v.model] ?? 'bg-zinc-700/30 text-zinc-300 border-zinc-600/30'}`}>
                {v.model}
              </span>
              <span className={`text-xs font-bold ${v.vote === 'ACCEPT' ? 'text-green-400' : 'text-red-400'}`}>
                {v.vote}
              </span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">{v.reasoning}</p>
            <div className="mt-2 text-right text-xs text-zinc-500">{v.confidence}% conf.</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EvaluationPanel({ ev, currSymbol }: { ev: EvaluationResult; currSymbol: string }) {
  const isAccept = ev.verdict === 'ACCEPT'
  return (
    <div className={`rounded-2xl p-5 border ${
      isAccept ? 'bg-green-950/20 border-green-700/30' : 'bg-yellow-950/20 border-yellow-700/30'
    }`}>
      <div className="flex items-center gap-3 mb-2">
        <span className="text-lg">{isAccept ? '✅' : '⚠️'}</span>
        <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Evaluator AI</h3>
        <span className={`ml-auto text-xs font-bold px-3 py-1 rounded-full border ${
          isAccept
            ? 'bg-green-500/20 text-green-400 border-green-500/40'
            : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40'
        }`}>{ev.verdict}</span>
      </div>
      <p className="text-sm text-zinc-300 mb-3">{ev.message}</p>
      <div className="flex flex-wrap gap-4 text-xs text-zinc-500">
        <span>Market: <strong className="text-zinc-300">{currSymbol}{ev.market_price?.toLocaleString()}</strong></span>
        <span>Fair range: <strong className="text-zinc-300">{currSymbol}{ev.fair_range?.[0]?.toLocaleString()} – {currSymbol}{ev.fair_range?.[1]?.toLocaleString()}</strong></span>
        <span>Deviation: <strong className={ev.deviation > 0 ? 'text-orange-400' : 'text-blue-400'}>{ev.deviation > 0 ? '+' : ''}{ev.deviation}%</strong></span>
        <span>Confidence: <strong className="text-zinc-300">{ev.confidence}%</strong></span>
      </div>
    </div>
  )
}

function RoundBubble({ log, currSymbol }: { log: RoundMessage; currSymbol: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-2"
    >
      {/* Round header */}
      <div className="flex items-center gap-2 px-1">
        <span className="text-xs text-zinc-600 font-mono">Round {log.round}</span>
        {log.strategy && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-violet-900/30 text-violet-400 border border-violet-700/30">
            {log.strategy}
          </span>
        )}
        <span className="text-xs text-zinc-600 ml-auto font-mono">
          gap <span className="text-zinc-400">{currSymbol}{log.gap?.toFixed(2)}</span>
        </span>
        {log.fraud_flag && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/40 text-red-400 border border-red-700/30 truncate max-w-[160px]" title={log.fraud_flag}>
            🚨 Fraud flag
          </span>
        )}
      </div>

      {/* Buyer bubble — left */}
      <div className="flex items-start gap-2">
        <div className="w-7 h-7 rounded-full bg-blue-700/40 border border-blue-600/40 flex items-center justify-center text-xs shrink-0 mt-0.5">
          B
        </div>
        <div className="bg-blue-950/50 border border-blue-700/30 rounded-2xl rounded-tl-sm px-4 py-2.5 max-w-[85%]">
          <div className="text-xs text-blue-400 font-semibold mb-1 flex items-center gap-2">
            Buyer
            <span className={`px-1.5 py-0.5 rounded text-[10px] border ${MODEL_COLORS[log.buyer_model] ?? 'bg-zinc-700/30 text-zinc-400 border-zinc-600/30'}`}>
              {log.buyer_model}
            </span>
          </div>
          <p className="text-sm text-zinc-200 leading-relaxed">{log.buyer_message}</p>
          <div className="text-right text-blue-300 font-mono font-bold mt-1 text-sm">{currSymbol}{log.buyer.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
      </div>

      {/* Seller bubble — right */}
      <div className="flex items-start gap-2 flex-row-reverse">
        <div className="w-7 h-7 rounded-full bg-violet-700/40 border border-violet-600/40 flex items-center justify-center text-xs shrink-0 mt-0.5">
          S
        </div>
        <div className="bg-violet-950/50 border border-violet-700/30 rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[85%]">
          <div className="text-xs text-violet-400 font-semibold mb-1 flex items-center gap-2 justify-end">
            <span className={`px-1.5 py-0.5 rounded text-[10px] border ${MODEL_COLORS[log.seller_model] ?? 'bg-zinc-700/30 text-zinc-400 border-zinc-600/30'}`}>
              {log.seller_model}
            </span>
            Seller
          </div>
          <p className="text-sm text-zinc-200 leading-relaxed text-right">{log.seller_message}</p>
          <div className="text-left text-violet-300 font-mono font-bold mt-1 text-sm">{currSymbol}{log.seller.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
      </div>
    </motion.div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function NegotiationPanel({ role, strategy = 'balanced', initialProduct, initialMaxPrice, initialMinPrice, onDeal, onReset }: Props) {
  const { currSymbol } = useCurrency()
  const [maxPrice,     setMaxPrice]     = useState(initialMaxPrice ?? 1000)
  const [minPrice,     setMinPrice]     = useState(initialMinPrice ?? 500)
  const [product,      setProduct]      = useState(initialProduct ?? 'Laptop')
  const [marketPrice,  setMarketPrice]  = useState(750)
  const [model,        setModel]        = useState('gemini')
  const [rounds,       setRounds]       = useState<RoundMessage[]>([])
  const roundsRef = useRef<RoundMessage[]>([])
  const [status,  setStatus]  = useState<'idle' | 'running' | 'done'>('idle')
  const [result,  setResult]  = useState<DoneMessage | null>(null)
  const [error,   setError]   = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const start = () => {
    if (minPrice >= maxPrice) { setError('Max price must be greater than min price'); return }
    if (marketPrice <= 0)     { setError('Market price must be positive'); return }
    setError('')
    setRounds([])
    roundsRef.current = []
    setResult(null)
    setStatus('running')

    const ws = connectNegotiation(
      {
        max_price:    maxPrice,
        min_price:    minPrice,
        buyer_model:  model,
        seller_model: model,
        strategy,
        product,
        market_price: marketPrice,
      },
      (data: WSMessage) => {
        if (data.type === 'round') {
          roundsRef.current = [...roundsRef.current, data as RoundMessage]
          setRounds([...roundsRef.current])
        } else if (data.type === 'done') {
          const done = data as DoneMessage
          setResult(done)
          setStatus('done')
          onDeal?.(done.final_price ?? 0, done.agreement, done.contract_hash ?? '', roundsRef.current)
        }
      },
      () => { setError('WebSocket connection failed'); setStatus('idle') }
    )
    wsRef.current = ws
  }

  const reset = () => {
    wsRef.current?.close()
    setRounds([])
    roundsRef.current = []
    setResult(null)
    setStatus('idle')
    setError('')
    onReset?.()
  }

  const fraudFlags = result?.fraud_flags?.filter(Boolean) ?? []

  return (
    <div className="flex flex-col gap-6">

      {/* ── Config Card ──────────────────────────────────────────────────── */}
      <div className="bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-6 grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Left column */}
        <div className="space-y-4">
          {/* Product */}
          <div>
            <label className="text-xs text-zinc-400 block mb-1 uppercase tracking-wider">🏷 Product Name</label>
            <input
              type="text"
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-xl px-4 py-3 text-white text-sm font-semibold outline-none focus:border-violet-500 transition"
              value={product}
              onChange={e => setProduct(e.target.value)}
              placeholder="e.g. Laptop, Car, House…"
            />
          </div>
          {/* Market Price */}
          <div>
            <label className="text-xs text-zinc-400 block mb-1 uppercase tracking-wider">📊 Market Price ({currSymbol}) — Evaluator Reference</label>
            <input
              type="number"
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-xl px-4 py-3 text-white text-lg font-semibold outline-none focus:border-violet-500 transition"
              value={marketPrice}
              onChange={e => setMarketPrice(+e.target.value)}
            />
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <div>
            <label className="text-xs text-zinc-400 block mb-1 uppercase tracking-wider">
              {role === 'buyer' ? `💰 Buyer Max Budget (${currSymbol})` : `🏷️ Seller Min Acceptable Price (${currSymbol})`}
            </label>
            <input
              type="number"
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-xl px-4 py-3 text-white text-lg font-semibold outline-none focus:border-violet-500 transition"
              value={role === 'buyer' ? maxPrice : minPrice}
              onChange={e => role === 'buyer' ? setMaxPrice(+e.target.value) : setMinPrice(+e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-zinc-400 block mb-1 uppercase tracking-wider">
              {role === 'buyer' ? `📉 Seller Min Price (${currSymbol})` : `📈 Buyer Max Budget (${currSymbol})`}
            </label>
            <input
              type="number"
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-xl px-4 py-3 text-white text-lg font-semibold outline-none focus:border-violet-500 transition"
              value={role === 'buyer' ? minPrice : maxPrice}
              onChange={e => role === 'buyer' ? setMinPrice(+e.target.value) : setMaxPrice(+e.target.value)}
            />
          </div>
          <ModelSelector value={model} onChange={setModel} />
          <div className="flex gap-3 pt-1">
            {status !== 'running' ? (
              <button
                onClick={start}
                className="flex-1 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold text-sm hover:opacity-90 transition"
              >
                ▶ Start Negotiation
              </button>
            ) : (
              <button
                onClick={reset}
                className="flex-1 py-3 rounded-xl bg-red-600/80 text-white font-semibold text-sm hover:bg-red-700 transition"
              >
                ✕ Stop
              </button>
            )}
            {status === 'done' && (
              <button onClick={reset} className="px-4 py-3 rounded-xl border border-zinc-600 text-zinc-400 text-sm hover:border-violet-500 hover:text-white transition">
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700/40 text-red-400 text-sm px-4 py-3 rounded-xl">{error}</div>
      )}

      {/* ── Fraud Flags ───────────────────────────────────────────────────── */}
      {fraudFlags.length > 0 && (
        <div className="bg-red-950/40 border border-red-700/40 rounded-2xl px-5 py-4 space-y-1">
          <div className="text-sm font-bold text-red-400 mb-2">🚨 Fraud / Safety Alerts</div>
          {fraudFlags.map((f, i) => (
            <div key={i} className="text-xs text-red-300 font-mono">{f}</div>
          ))}
        </div>
      )}

      {/* ── Result Banner ─────────────────────────────────────────────────── */}
      {result && (
        <div className={`rounded-2xl px-6 py-4 border flex flex-col sm:flex-row items-start sm:items-center gap-4 ${
          result.agreement
            ? 'bg-green-950/40 border-green-700/40'
            : 'bg-red-950/40 border-red-700/40'
        }`}>
          <div>
            <div className={`text-2xl font-bold ${result.agreement ? 'text-green-400' : 'text-red-400'}`}>
              {result.agreement ? '✅ Deal Reached!' : '❌ No Agreement'}
            </div>
            {result.agreement && (
              <div className="text-white font-semibold text-lg mt-0.5">
                Final Price: <span className="text-green-400">{currSymbol}{result.final_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="text-xs text-zinc-500 mt-1 space-x-3">
              {result.rounds_taken && <span>Rounds: {result.rounds_taken}</span>}
              {result.strategy_switched && <span>⚡ Strategy was switched</span>}
              {result.memory_hint?.has_memory && (
                <span>📚 Avg past price: {currSymbol}{result.memory_hint.avg_accepted_price?.toLocaleString('en-IN')}</span>
              )}
            </div>
          </div>
          {result.contract_hash && (
            <div className="ml-auto text-right">
              <div className="text-xs text-zinc-500 mb-1">Contract Hash</div>
              <div className="text-xs text-violet-400 font-mono break-all max-w-xs">{result.contract_hash}</div>
            </div>
          )}
        </div>
      )}

      {/* ── Evaluator + Votes (shown after deal) ──────────────────────────── */}
      {result?.agreement && result.evaluation?.verdict && (
        <EvaluationPanel ev={result.evaluation} currSymbol={currSymbol} />
      )}
      {result?.agreement && result.votes?.votes?.length ? (
        <VotesPanel votes={result.votes} />
      ) : null}

      {/* ── Live AI Chat Stream ───────────────────────────────────────────── */}
      <div className="bg-[#0d0d1a] border border-[#2a2a45] rounded-2xl p-6 flex flex-col" style={{ minHeight: '520px' }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-white">💬 Live AI Negotiation</h2>
          {status === 'running' && (
            <span className="flex items-center gap-2 text-xs text-green-400">
              <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Live
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          <AnimatePresence initial={false}>
            {rounds.length === 0 && status === 'idle' && (
              <motion.p key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="text-zinc-500 text-sm mt-6 text-center">
                Configure the details above and press{' '}
                <span className="text-violet-400 font-medium">Start Negotiation</span> to watch the AIs negotiate.
              </motion.p>
            )}
            {rounds.map((log) => (
              <RoundBubble key={log.round} log={log} currSymbol={currSymbol} />
            ))}
            {status === 'running' && (
              <motion.div key="typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="flex items-center gap-2 text-violet-400 text-xs px-2 pt-1">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:300ms]" />
                </span>
                AI agents negotiating round {rounds.length + 1}…
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── Offer Convergence Graph ───────────────────────────────────────── */}
      <div className="bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">📈 Offer Convergence</h3>
        <OfferGraph
          logs={rounds}
          minPrice={minPrice}
          maxPrice={maxPrice}
          finalPrice={result?.final_price}
        />
      </div>

    </div>
  )
}
