'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency } from '@/context/CurrencyContext'

interface PrefQuestion { id: string; label: string; emoji: string; options: string[] }
interface ParsedQuery {
  original: string; category: string; budget: number | null; currency: string
  search_terms: string; has_preferences: boolean; preference_questions: PrefQuestion[]
}
interface Listing {
  listing_id: string
  product: { id: string; name: string; category: string; emoji: string }
  seller_name: string; price: number; rating: number; review_count: number
  trust_score: number; rank_score: number; verified: boolean; condition: string; stock: number
  url?: string
}
interface PipelineResult {
  listings: Listing[]; products_found: number; listings_found: number; query: string
  assistant_context?: { original_query: string; parsed: ParsedQuery; preferences: Record<string, string> }
}

const EXAMPLE_QUERIES = [
  'Gaming laptop under ₹90,000',
  'iPhone under $800',
  'Sony noise-cancelling headphones',
  '4K OLED TV 65 inch under $1500',
  'Mirrorless camera for beginners',
  'DJI drone for photography',
]

type AssistStep = 'query' | 'prefs' | 'results'

export default function AIResultsPage() {
  const router = useRouter()
  const { currSymbol } = useCurrency()
  const [step, setStep] = useState<AssistStep>('query')
  const [queryText, setQueryText] = useState('')
  const [parsed, setParsed] = useState<ParsedQuery | null>(null)
  const [prefs, setPrefs] = useState<Record<string, string>>({})
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<string | null>(null)



  const parseQuery = async () => {
    if (!queryText.trim()) return
    setError(''); setLoading(true)
    try {
      const r = await API.post('/pipeline/assistant/parse', { query: queryText })
      setParsed(r.data)
      setStep(r.data.has_preferences ? 'prefs' : 'results')
      if (!r.data.has_preferences) await discover({})
    } catch { setError('Could not parse query.') }
    finally { setLoading(false) }
  }

  const discover = async (overridePrefs?: Record<string, string>) => {
    const finalPrefs = overridePrefs ?? prefs
    setLoading(true); setError('')
    try {
      const r = await API.post('/pipeline/assistant/discover', {
        query: queryText, preferences: finalPrefs, limit: 8,
      })
      setResult(r.data); setStep('results')
    } catch { setError('Discovery failed.') }
    finally { setLoading(false) }
  }

  const reset = () => {
    setStep('query'); setParsed(null); setPrefs({}); setResult(null); setError(''); setSelected(null)
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="🤖 AI Results" />
      <main className="flex-1 overflow-y-auto p-6 space-y-5 max-w-3xl mx-auto w-full">

        {/* ── STEP 1: Query ── */}
        {step === 'query' && (
          <>
            <div className="bg-linear-to-br from-violet-950/40 to-blue-950/40 border border-violet-500/20 rounded-2xl p-8 text-center">
              <p className="text-3xl mb-3">🤖</p>
              <h2 className="text-2xl font-bold text-white mb-2">AI Shopping Assistant</h2>
              <p className="text-zinc-400 text-sm mb-6">
                Tell the AI what you need. It will understand your intent, ask smart questions, and surface the best deals.
              </p>
              <div className="max-w-xl mx-auto flex gap-2">
                <input
                  type="text" value={queryText}
                  onChange={e => setQueryText(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && parseQuery()}
                  placeholder='"I want a gaming laptop under ₹90,000"'
                  className="flex-1 bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-violet-500 transition"
                />
                <button
                  onClick={parseQuery} disabled={loading || !queryText.trim()}
                  className="px-5 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition flex items-center gap-2 whitespace-nowrap"
                >
                  {loading
                    ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Parsing…</>
                    : '→ Find Deals'}
                </button>
              </div>
              {error && <p className="text-red-400 text-xs mt-3">{error}</p>}
            </div>

            <div>
              <p className="text-xs text-zinc-600 mb-2 uppercase tracking-wider">Try an example:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUERIES.map(q => (
                  <button key={q} onClick={() => setQueryText(q)}
                    className="px-3 py-1.5 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-violet-500/40 rounded-lg text-xs transition">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* ── STEP 2: Preferences ── */}
        {step === 'prefs' && parsed && (
          <>
            <div className="flex items-center gap-3">
              <button onClick={() => setStep('query')}
                className="text-zinc-400 hover:text-white text-sm transition">← Back</button>
              <div className="px-3 py-1.5 bg-green-900/20 border border-green-700/30 rounded-lg text-xs text-green-400">
                ✅ <span className="font-semibold text-white ml-1">{parsed.original}</span>
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 bg-violet-900/30 border border-violet-700/30 rounded-xl flex items-center justify-center text-2xl">🎯</div>
              <div>
                <p className="text-white font-semibold capitalize">{parsed.category.replace(/_/g, ' ')}</p>
                <p className="text-zinc-400 text-sm">
                  {parsed.budget
                        ? `Budget: ${currSymbol}${parsed.budget.toLocaleString()}`
                    : 'No budget constraint — all price ranges'}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <p className="text-sm text-zinc-400">Refine your preferences (optional):</p>
              {parsed.preference_questions.map(q => (
                <div key={q.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <p className="text-sm font-semibold text-zinc-300 mb-3">{q.emoji} {q.label}</p>
                  <div className="flex flex-wrap gap-2">
                    {q.options.map(opt => {
                      const active = prefs[q.id] === opt
                      return (
                        <button key={opt}
                          onClick={() => setPrefs(p => ({ ...p, [q.id]: active ? '' : opt }))}
                          className={`px-3 py-1.5 rounded-lg border text-sm transition ${
                            active ? 'border-violet-500 bg-violet-900/40 text-white font-semibold'
                            : 'border-gray-700 text-zinc-400 hover:border-violet-500/40 hover:text-white'
                          }`}>
                          {opt}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={() => discover()} disabled={loading}
              className="w-full py-3.5 bg-linear-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 disabled:opacity-50 text-white font-bold rounded-xl transition flex items-center justify-center gap-2"
            >
              {loading
                ? <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Running AI Pipeline…</>
                : '🚀 Find Best Deals'}
            </button>
          </>
        )}

        {/* ── STEP 3: Results ── */}
        {step === 'results' && result && (
          <>
            <div className="flex items-center gap-3">
              <button onClick={reset} className="text-zinc-400 hover:text-white text-sm transition">← New Search</button>
              <div className="px-3 py-1.5 bg-violet-900/20 border border-violet-700/30 rounded-lg text-xs text-violet-300">
                🎯 AI Results for: <span className="font-semibold text-white">{result.query}</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: '📦 Products', value: result.products_found },
                { label: '🏪 Listings', value: result.listings_found },
                { label: '💰 Best Price', value: result.listings.length ? `${currSymbol}${Math.min(...result.listings.map(l => l.price)).toFixed(0)}` : '—' },
              ].map(s => (
                <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <p className="text-zinc-500 text-xs">{s.label}</p>
                  <p className="text-white font-bold text-xl mt-1">{s.value}</p>
                </div>
              ))}
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-800">
                <h3 className="font-semibold text-white text-sm">🤖 AI-Ranked Results</h3>
              </div>
              {result.listings.map((l, i) => (
                <div
                  key={l.listing_id}
                  onClick={() => setSelected(selected === l.listing_id ? null : l.listing_id)}
                  className={`flex items-center gap-4 px-5 py-4 cursor-pointer border-b border-gray-800 transition ${
                    selected === l.listing_id ? 'bg-violet-950/30 border-l-2 border-l-violet-500' : 'hover:bg-white/2'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                    i === 0 ? 'bg-yellow-500/20 text-yellow-400' : i === 1 ? 'bg-zinc-600/20 text-zinc-300' :
                    i === 2 ? 'bg-orange-800/20 text-orange-400' : 'bg-gray-800 text-zinc-600'
                  }`}>#{i + 1}</div>
                  <div className="w-11 h-11 bg-gray-800 rounded-xl flex items-center justify-center text-2xl shrink-0">{l.product.emoji}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-semibold text-sm">{l.product.name}</p>
                    <p className="text-zinc-500 text-xs mt-0.5">
                      🏪 {l.seller_name} · {l.condition}
                      {l.verified && <span className="text-green-400 ml-1">✓</span>}
                      {' · '}⭐ {l.rating.toFixed(1)} ({l.review_count.toLocaleString()})
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-white font-bold">{currSymbol}{l.price.toFixed(2)}</p>
                    <p className="text-zinc-600 text-[10px]">{l.stock} left</p>
                  </div>
                  <div className={`w-12 h-12 rounded-xl border flex flex-col items-center justify-center shrink-0 ${
                    l.rank_score >= 70 ? 'border-green-500/40 bg-green-500/10' : 'border-gray-700 bg-gray-800/40'
                  }`}>
                    <span className="text-[9px] text-zinc-500">AI</span>
                    <span className={`text-sm font-bold ${l.rank_score >= 70 ? 'text-green-300' : 'text-zinc-400'}`}>
                      {l.rank_score.toFixed(0)}
                    </span>
                  </div>
                  {selected === l.listing_id && (
                    <div className="flex flex-col gap-1 shrink-0">
                      {l.url && (
                        <a
                          href={l.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={e => e.stopPropagation()}
                          className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-zinc-300 text-xs font-bold rounded-lg transition whitespace-nowrap text-center"
                        >
                          🔗 View
                        </a>
                      )}
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          router.push(`/dashboard/negotiation-room?product=${encodeURIComponent(l.product.name)}&max=${l.price}&min=${Math.round(l.price * 0.75 * 100) / 100}`)
                        }}
                        className="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold rounded-lg transition whitespace-nowrap"
                      >
                        🤝 Negotiate
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
