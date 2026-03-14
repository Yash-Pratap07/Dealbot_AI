'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency, CURRENCIES } from '@/context/CurrencyContext'
interface Product { id: string; name: string; category: string; emoji: string; image?: string }
interface Listing {
  listing_id: string; product: Product; seller_name: string
  price: number; currency: string; rating: number; review_count: number
  trust_score: number; rank_score: number; verified: boolean
  condition: string; stock: number; image?: string; url?: string
}
interface SecondHand {
  title: string; price: number; currency: string; source: string
  url: string; image: string; condition: string; rating: number; snippet: string
}
interface PipelineResult {
  listings: Listing[]; products_found: number; listings_found: number
  data_source?: string; web_search_enabled?: boolean
  secondhand?: SecondHand[]
}

const EXAMPLES = [
  'iPhone 16 Pro', 'Sony WH-1000XM6', 'MacBook Pro M4',
  'RTX 5090 GPU', 'DJI Mini 4 Pro', 'Samsung Galaxy S25',
]


function Stars({ rating }: { rating: number }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span className="inline-flex items-center gap-0.5 text-yellow-400 text-xs">
      {'★'.repeat(full)}{half ? '½' : ''}{'☆'.repeat(5 - full - (half ? 1 : 0))}
      <span className="text-zinc-400 ml-1">{rating.toFixed(1)}</span>
    </span>
  )
}

function ProductImage({ src, emoji, alt }: { src?: string; emoji: string; alt: string }) {
  const [err, setErr] = useState(false)
  if (src && !err) {
    return (
      <img
        src={src} alt={alt}
        onError={() => setErr(true)}
        className="w-full h-44 object-contain bg-white rounded-t-2xl p-3"
      />
    )
  }
  return (
    <div className="w-full h-44 bg-gradient-to-br from-gray-800 to-gray-900 rounded-t-2xl flex items-center justify-center text-5xl">
      {emoji}
    </div>
  )
}

export default function SearchProductPage() {
  const router = useRouter()
  const { currency, currSymbol } = useCurrency()
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'new' | 'used'>('new')

  const formatPrice = (price: number, cur?: string) => {
    const sym = CURRENCIES.find(c => c.code === (cur ?? currency))?.symbol ?? currSymbol
    return `${sym}${price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  }

  const search = async (term?: string) => {
    const query = term ?? q
    if (!query.trim()) return
    if (term) setQ(term)
    setLoading(true); setError(''); setResult(null); setTab('new')
    try {
      const r = await API.get('/pipeline/search/public', { params: { q: query, limit: 8, currency } })
      setResult(r.data)
    } catch { setError('Search failed. Make sure the backend is running.') }
    finally { setLoading(false) }
  }

  const secondhand = result?.secondhand ?? []

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="🔍 Search Products" />
      <main className="flex-1 overflow-y-auto p-6 space-y-5 max-w-6xl mx-auto w-full">

        {/* Search hero */}
        <div className="bg-gradient-to-r from-violet-950/40 to-blue-950/40 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-bold text-white mb-1">Find the Best Product Deal</h2>
          <p className="text-zinc-500 text-sm mb-4">
            Our AI pipeline discovers products, compares prices, and ranks sellers — instantly.
          </p>
          <div className="flex gap-3">
            <input
              type="text" value={q}
              onChange={e => setQ(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
              placeholder={`e.g. "Sony headphones", "gaming laptop under ${currSymbol}90000"…`}
              className="flex-1 bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-violet-500 transition"
            />
            <button
              onClick={() => search()} disabled={loading || !q.trim()}
              className="px-6 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition flex items-center gap-2"
            >
              {loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Searching…</>
                : '🚀 Search'}
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            {EXAMPLES.map(e => (
              <button key={e} onClick={() => search(e)}
                className="px-3 py-1 bg-gray-800/60 border border-gray-700 text-zinc-400 hover:text-white hover:border-violet-500/40 rounded-lg text-xs transition">
                {e}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 bg-red-950/40 border border-red-700/40 rounded-xl text-red-400 text-sm">{error}</div>
        )}

        {/* Stats */}
        {result && (
          <>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: '📦 Products', value: result.products_found, color: 'text-white' },
                { label: '🏪 Listings', value: result.listings_found, color: 'text-blue-400' },
                { label: '💰 Best Price', value: formatPrice(Math.min(...result.listings.map(l => l.price))), color: 'text-green-400' },
                { label: '♻️ Used Options', value: secondhand.length, color: 'text-amber-400' },
              ].map(s => (
                <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <p className="text-zinc-500 text-xs">{s.label}</p>
                  <p className={`font-bold text-xl mt-1 ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>

            {/* Tabs — New vs Second-hand */}
            <div className="flex gap-2 border-b border-gray-800 pb-0">
              <button
                onClick={() => setTab('new')}
                className={`px-5 py-2.5 text-sm font-semibold rounded-t-xl transition ${
                  tab === 'new'
                    ? 'bg-gray-900 text-white border border-gray-800 border-b-transparent -mb-px'
                    : 'text-zinc-500 hover:text-white'
                }`}
              >
                🛒 New Products ({result.listings.length})
              </button>
              <button
                onClick={() => setTab('used')}
                className={`px-5 py-2.5 text-sm font-semibold rounded-t-xl transition ${
                  tab === 'used'
                    ? 'bg-gray-900 text-amber-400 border border-gray-800 border-b-transparent -mb-px'
                    : 'text-zinc-500 hover:text-amber-400'
                }`}
              >
                ♻️ Second Hand / Refurbished ({secondhand.length})
              </button>
            </div>

            {/* ── NEW product cards grid ── */}
            {tab === 'new' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {result.listings.map((l, i) => (
                  <div
                    key={l.listing_id}
                    className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden hover:border-violet-600/50 hover:shadow-lg hover:shadow-violet-500/5 transition group relative"
                  >
                    {/* Rank badge */}
                    {i < 3 && (
                      <div className={`absolute top-3 left-3 z-10 w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                        i === 0 ? 'bg-yellow-500/90 text-black' :
                        i === 1 ? 'bg-zinc-400/90 text-black' : 'bg-orange-600/90 text-white'
                      }`}>#{i + 1}</div>
                    )}
                    {l.verified && (
                      <div className="absolute top-3 right-3 z-10 px-2 py-0.5 bg-green-600/90 text-white text-[10px] font-bold rounded-md">✓ Verified</div>
                    )}

                    {/* Image */}
                    <ProductImage
                      src={l.image || l.product.image}
                      emoji={l.product.emoji}
                      alt={l.product.name}
                    />

                    {/* Content */}
                    <div className="p-4 space-y-2">
                      <h3 className="text-white font-semibold text-sm leading-tight line-clamp-2 min-h-[2.5rem]">
                        {l.product.name}
                      </h3>

                      <div className="flex items-center justify-between">
                        <Stars rating={l.rating} />
                        <span className="text-zinc-500 text-[10px]">({l.review_count.toLocaleString()})</span>
                      </div>

                      {/* Price */}
                      <div className="flex items-end gap-2">
                        <span className="text-white font-bold text-xl">{formatPrice(l.price, l.currency)}</span>
                      </div>

                      {/* Meta */}
                      <div className="flex items-center gap-2 flex-wrap text-[10px]">
                        <span className="px-1.5 py-0.5 bg-gray-800 rounded text-zinc-400 border border-gray-700">{l.condition}</span>
                        <span className="px-1.5 py-0.5 bg-gray-800 rounded text-zinc-400 border border-gray-700">🏪 {l.seller_name}</span>
                        <span className="text-zinc-500">{l.stock} in stock</span>
                      </div>

                      {/* Trust + AI score bar */}
                      <div className="flex items-center gap-3 pt-1">
                        <div className="flex-1">
                          <div className="flex items-center gap-1">
                            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${l.trust_score >= 80 ? 'bg-green-500' : l.trust_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                style={{ width: `${l.trust_score}%` }}
                              />
                            </div>
                            <span className="text-[9px] text-zinc-500 w-8">T:{l.trust_score.toFixed(0)}</span>
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded-lg text-xs font-bold ${
                          l.rank_score >= 70
                            ? 'bg-green-900/40 text-green-400 border border-green-700/30'
                            : 'bg-gray-800 text-zinc-500 border border-gray-700'
                        }`}>
                          AI {l.rank_score.toFixed(0)}
                        </div>
                      </div>

                      {/* CTA */}
                      <div className="flex gap-2 mt-2">
                        {l.url && (
                          <a
                            href={l.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 py-2.5 text-center bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-violet-500/40 text-zinc-300 hover:text-white text-xs font-bold rounded-xl transition"
                          >
                            🔗 View on Site
                          </a>
                        )}
                        <button
                          onClick={() =>
                            router.push(`/dashboard/negotiation-room?product=${encodeURIComponent(l.product.name)}&max=${l.price}&min=${Math.round(l.price * 0.75 * 100) / 100}`)
                          }
                          className={`${l.url ? 'flex-1' : 'w-full'} py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-xs font-bold rounded-xl transition`}
                        >
                          🤝 Negotiate This Deal
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── SECOND-HAND / REFURBISHED cards ── */}
            {tab === 'used' && (
              secondhand.length === 0 ? (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-14 text-center">
                  <div className="text-4xl mb-3">♻️</div>
                  <p className="text-zinc-400 text-sm">No second-hand options found for &ldquo;{q}&rdquo;.</p>
                  <p className="text-zinc-600 text-xs mt-1">Try searching for a more popular product.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-amber-400/70 flex items-center gap-2">
                    <span>♻️</span> AI-discovered used &amp; refurbished listings from across the web
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {secondhand.map((sh, i) => (
                      <div key={i} className="bg-gray-900 border border-amber-900/30 rounded-2xl overflow-hidden hover:border-amber-600/50 transition">
                        {/* Image */}
                        <ProductImage src={sh.image} emoji="♻️" alt={sh.title} />
                        <div className="p-4 space-y-2">
                          <h3 className="text-white font-semibold text-sm leading-tight line-clamp-2 min-h-[2.5rem]">
                            {sh.title}
                          </h3>
                          {sh.snippet && (
                            <p className="text-zinc-500 text-xs line-clamp-2">{sh.snippet}</p>
                          )}
                          <div className="flex items-center justify-between">
                            <Stars rating={sh.rating} />
                            <span className="px-1.5 py-0.5 bg-amber-900/30 rounded text-amber-400 text-[10px] border border-amber-700/30">
                              {sh.condition}
                            </span>
                          </div>
                          <div className="flex items-end gap-2">
                            <span className="text-white font-bold text-xl">{formatPrice(sh.price, sh.currency)}</span>
                          </div>
                          <p className="text-zinc-500 text-[10px]">🏪 {sh.source}</p>
                          <div className="flex gap-2 mt-1">
                            {sh.url && (
                              <a
                                href={sh.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 py-2 text-center bg-amber-700/30 hover:bg-amber-700/50 border border-amber-700/40 text-amber-300 text-xs font-bold rounded-xl transition"
                              >
                                🔗 View Listing
                              </a>
                            )}
                            <button
                              onClick={() =>
                                router.push(`/dashboard/negotiation-room?product=${encodeURIComponent(sh.title)}&max=${sh.price}&min=${Math.round(sh.price * 0.6 * 100) / 100}`)
                              }
                              className="flex-1 py-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold rounded-xl transition"
                            >
                              🤝 Negotiate
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}
          </>
        )}

        {!result && !loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-16 text-center">
            <div className="text-5xl mb-4">🛍️</div>
            <p className="text-white font-semibold text-lg mb-1">Search any product</p>
            <p className="text-zinc-500 text-sm">Our AI pipeline ranks results by price, trust, and availability.</p>
          </div>
        )}
      </main>
    </div>
  )
}
