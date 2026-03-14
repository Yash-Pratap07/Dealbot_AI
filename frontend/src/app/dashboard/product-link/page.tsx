'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency } from '@/context/CurrencyContext'

interface Listing {
  listing_id: string
  product: { id: string; name: string; category: string; emoji: string; image?: string }
  seller_name: string; price: number; currency?: string; rating: number; review_count: number
  trust_score: number; rank_score: number; verified: boolean
  condition: string; stock: number; image?: string; url?: string
  cheaper_than_original?: boolean; savings?: number
}
interface SecondHand {
  title: string; price: number; currency: string; source: string
  url: string; image: string; condition: string; rating: number; snippet: string
}
interface PipelineResult {
  listings: Listing[]
  products_found: number; listings_found: number
  cheaper_count?: number; max_savings?: number; platform_price?: number
  secondhand?: SecondHand[]
}
interface ExtractedProduct {
  name: string; emoji: string; category: string; description: string
  image?: string; rating?: number; review_count?: number
  scraped_live?: boolean
  platform: { id: string; name: string; icon: string; currency: string }
  platform_price: number; currency: string; original_url: string
  specs: { key: string; value: string }[]
}

const EXAMPLE_URLS = [
  'https://www.amazon.in/Apple-iPhone-256GB/dp/B0CKDJ5R5Q',
  'https://www.amazon.com/Sony-WH1000XM6/dp/B0D98XAMPLE',
  'https://www.flipkart.com/asus-rog-gaming-laptop/p/itm123456',
]

const ANALYZING_MSGS = [
  '🔍 Fetching product page…',
  '📦 Extracting product data…',
  '🌐 Searching alternatives…',
  '🤖 AI ranking analysis…',
]

function detectPlatform(url: string) {
  const u = url.toLowerCase()
  if (u.includes('amazon.in'))  return '🛒 Amazon India'
  if (u.includes('amazon.com')) return '🛒 Amazon US'
  if (u.includes('flipkart'))   return '🛍️ Flipkart'
  if (u.includes('ebay'))       return '⚡ eBay'
  if (u.includes('bestbuy'))    return '💻 Best Buy'
  if (u.includes('apple.com'))  return '🍎 Apple Store'
  if (u.includes('myntra'))     return '👔 Myntra'
  if (u.includes('croma'))      return '⚡ Croma'
  if (u.startsWith('http'))     return '🌐 Online Store'
  return ''
}

function detectCurrency(url: string): string {
  const u = url.toLowerCase()
  if (u.includes('amazon.in') || u.includes('flipkart') || u.includes('croma') ||
      u.includes('reliancedigital') || u.includes('myntra') || u.includes('snapdeal') ||
      u.includes('meesho') || u.includes('tatacliq'))
    return 'INR'
  if (u.includes('amazon.co.uk') || u.includes('ebay.co.uk')) return 'GBP'
  if (u.includes('amazon.de') || u.includes('amazon.fr'))     return 'EUR'
  return 'INR'
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: '₹', USD: '$', GBP: '£', EUR: '€',
}
function sym(cur?: string) { return CURRENCY_SYMBOLS[cur || 'INR'] || '₹' }

type Step = 'input' | 'analyzing' | 'results'

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

export default function ProductLinkPage() {
  const router = useRouter()
  const { currSymbol } = useCurrency()
  const [url, setUrl] = useState('')
  const [step, setStep] = useState<Step>('input')
  const [analyzingIdx, setAnalyzingIdx] = useState(0)
  const [detectedPlat, setDetectedPlat] = useState('')
  const [extracted, setExtracted] = useState<ExtractedProduct | null>(null)
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [error, setError] = useState('')
  const [altTab, setAltTab] = useState<'new' | 'used'>('new')

  const secondhand = result?.secondhand ?? []

  const formatPrice = (price: number, cur?: string) => {
    const s = sym(cur)
    return `${s}${price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  }

  const analyze = async () => {
    if (!url.trim() || !url.startsWith('http')) {
      setError('Please enter a valid URL starting with http://'); return
    }
    setError(''); setStep('analyzing')
    for (let i = 0; i < ANALYZING_MSGS.length; i++) {
      setAnalyzingIdx(i); await delay(900)
    }
    try {
      const currency = detectCurrency(url)
      const r = await API.post('/pipeline/analyze-link', { url, limit: 5, currency })
      setExtracted(r.data.product)
      setResult(r.data.alternatives)
      setStep('results')
    } catch { setError('Failed to analyze the link.'); setStep('input') }
  }

  const reset = () => {
    setStep('input'); setExtracted(null); setResult(null); setUrl(''); setError(''); setDetectedPlat('')
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="🔗 Product Link Analyzer" />
<main className="flex-1 overflow-y-auto p-6 space-y-5 max-w-5xl mx-auto w-full">

        {/* ── INPUT ── */}
        {step === 'input' && (
          <>
            <div className="bg-linear-to-br from-orange-950/30 to-pink-950/30 border border-orange-500/20 rounded-2xl p-8 text-center">
              <p className="text-3xl mb-3">🔗</p>
              <h2 className="text-2xl font-bold text-white mb-2">Paste a Product Link</h2>
              <p className="text-zinc-400 text-sm mb-6">
                We&apos;ll extract product data and find cheaper alternatives across the web.
              </p>
              <div className="max-w-xl mx-auto space-y-3">
                <input
                  type="url" value={url}
                  onChange={e => { setUrl(e.target.value); setDetectedPlat(detectPlatform(e.target.value)) }}
                  placeholder="https://www.amazon.in/product/…"
                  className="w-full bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-orange-500 transition"
                />
                {detectedPlat && (
                  <div className="flex items-center gap-2 text-xs text-orange-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
                    Detected: <span className="font-semibold">{detectedPlat}</span>
                  </div>
                )}
                {error && <p className="text-red-400 text-xs">{error}</p>}
                <button
                  onClick={analyze} disabled={!url.trim()}
                  className="w-full py-3 bg-linear-to-r from-orange-600 to-pink-600 hover:from-orange-500 hover:to-pink-500 disabled:opacity-50 text-white font-bold rounded-xl transition"
                >
                  🔍 Analyze &amp; Find Alternatives
                </button>
              </div>
            </div>

            <div>
              <p className="text-xs text-zinc-600 mb-2 uppercase tracking-wider">Try an example URL:</p>
              <div className="space-y-2">
                {EXAMPLE_URLS.map(u => (
                  <button key={u} onClick={() => { setUrl(u); setDetectedPlat(detectPlatform(u)) }}
                    className="w-full text-left px-3 py-2 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-orange-500/40 rounded-lg text-xs font-mono transition truncate">
                    {u}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* ── ANALYZING ── */}
        {step === 'analyzing' && (
          <div className="flex flex-col items-center justify-center py-20 gap-6">
            <div className="w-16 h-16 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
            <div className="text-center space-y-2">
              <p className="text-white font-semibold text-lg">Analyzing Product Link…</p>
              {ANALYZING_MSGS.map((msg, i) => (
                <p key={i} className={`text-sm transition-all ${
                  i < analyzingIdx ? 'text-green-400' : i === analyzingIdx ? 'text-white animate-pulse' : 'text-zinc-700'
                }`}>
                  {i < analyzingIdx ? '✓' : i === analyzingIdx ? '⟳' : '○'} {msg}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* ── RESULTS ── */}
        {step === 'results' && extracted && result && (
          <>
            <button onClick={reset} className="text-zinc-400 hover:text-white text-sm flex items-center gap-1 transition">
              ← Analyze Another Link
            </button>

            {/* Original Product card */}
            <div className="bg-linear-to-r from-orange-950/40 to-pink-950/40 border border-orange-500/20 rounded-2xl p-5">
              <p className="text-xs text-orange-400 uppercase tracking-wider mb-3 font-semibold">
                {extracted.platform.icon} Original Listing — {extracted.platform.name}
              </p>
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-gray-800 border border-gray-700 rounded-xl flex items-center justify-center text-3xl shrink-0 overflow-hidden">
                  {extracted.image
                    // eslint-disable-next-line @next/next/no-img-element
                    ? <img src={extracted.image} alt={extracted.name} className="w-full h-full object-cover" />
                    : extracted.emoji}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-white font-bold text-lg">{extracted.name}</h3>
                    {extracted.scraped_live
                      ? <span className="text-[10px] px-2 py-0.5 bg-green-900/40 border border-green-700/40 text-green-400 rounded-full font-semibold">✓ Live Price</span>
                      : <span className="text-[10px] px-2 py-0.5 bg-yellow-900/30 border border-yellow-700/30 text-yellow-500 rounded-full">~ Estimated</span>}
                  </div>
                  <p className="text-zinc-400 text-sm mt-0.5">{extracted.description}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {extracted.specs.map(s => (
                      <span key={s.key} className="text-xs px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-zinc-400">
                        {s.key}: <span className="text-white">{s.value}</span>
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-zinc-500 text-xs">Listed at</p>
                  <p className="text-2xl font-bold text-white">{sym(extracted.currency)}{extracted.platform_price.toLocaleString('en-IN')}</p>
                  <p className="text-xs text-zinc-500">{extracted.currency}</p>
                </div>
              </div>
              {(result.max_savings ?? 0) > 0 && (
                <div className="mt-4 px-4 py-2.5 bg-green-900/30 border border-green-700/30 rounded-xl text-sm text-green-300">
                  🎉 Found <strong>{result.cheaper_count}</strong> cheaper alternative{result.cheaper_count !== 1 ? 's' : ''}!
                  Save up to <strong className="text-green-200">{sym(extracted.currency)}{((result.max_savings ?? 0)).toLocaleString('en-IN')}</strong>
                </div>
              )}
            </div>

            {/* Tabs — Alternatives vs Second-hand */}
            <div className="flex gap-2 border-b border-gray-800 pb-0">
              <button
                onClick={() => setAltTab('new')}
                className={`px-5 py-2.5 text-sm font-semibold rounded-t-xl transition ${
                  altTab === 'new'
                    ? 'bg-gray-900 text-white border border-gray-800 border-b-transparent -mb-px'
                    : 'text-zinc-500 hover:text-white'
                }`}
              >
                🤖 AI Alternatives ({result.listings.length})
              </button>
              <button
                onClick={() => setAltTab('used')}
                className={`px-5 py-2.5 text-sm font-semibold rounded-t-xl transition ${
                  altTab === 'used'
                    ? 'bg-gray-900 text-amber-400 border border-gray-800 border-b-transparent -mb-px'
                    : 'text-zinc-500 hover:text-amber-400'
                }`}
              >
                ♻️ Second Hand ({secondhand.length})
              </button>
            </div>

            {/* ── NEW alternatives card grid ── */}
            {altTab === 'new' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.listings.map((l, i) => (
                  <div
                    key={l.listing_id}
                    className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden hover:border-violet-600/50 hover:shadow-lg hover:shadow-violet-500/5 transition group relative"
                  >
                    {i < 3 && (
                      <div className={`absolute top-3 left-3 z-10 w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                        i === 0 ? 'bg-yellow-500/90 text-black' :
                        i === 1 ? 'bg-zinc-400/90 text-black' : 'bg-orange-600/90 text-white'
                      }`}>#{i + 1}</div>
                    )}
                    {l.cheaper_than_original && l.savings != null && l.savings > 0 && (
                      <div className="absolute top-3 right-3 z-10 px-2 py-0.5 bg-green-600/90 text-white text-[10px] font-bold rounded-md">
                        SAVE {formatPrice(l.savings, extracted.currency)}
                      </div>
                    )}

                    <ProductImage
                      src={l.image || l.product.image}
                      emoji={l.product.emoji}
                      alt={l.product.name}
                    />

                    <div className="p-4 space-y-2">
                      <h3 className="text-white font-semibold text-sm leading-tight line-clamp-2 min-h-[2.5rem]">
                        {l.product.name}
                      </h3>
                      <div className="flex items-center justify-between">
                        <Stars rating={l.rating} />
                        <span className="text-zinc-500 text-[10px]">({l.review_count.toLocaleString()})</span>
                      </div>
                      <div className="flex items-end gap-2">
                        <span className="text-white font-bold text-xl">{formatPrice(l.price, extracted.currency)}</span>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap text-[10px]">
                        <span className="px-1.5 py-0.5 bg-gray-800 rounded text-zinc-400 border border-gray-700">{l.condition}</span>
                        <span className="px-1.5 py-0.5 bg-gray-800 rounded text-zinc-400 border border-gray-700">🏪 {l.seller_name}</span>
                        {l.verified && <span className="text-green-400">✓ Verified</span>}
                      </div>
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
                          onClick={() => router.push(`/dashboard/negotiation-room?product=${encodeURIComponent(l.product.name)}&max=${l.price}&min=${Math.round(l.price * 0.75 * 100) / 100}`)}
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
            {altTab === 'used' && (
              secondhand.length === 0 ? (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-14 text-center">
                  <div className="text-4xl mb-3">♻️</div>
                  <p className="text-zinc-400 text-sm">No second-hand options found for this product.</p>
                  <p className="text-zinc-600 text-xs mt-1">Try a more popular product for used listings.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-amber-400/70 flex items-center gap-2">
                    <span>♻️</span> AI-discovered used &amp; refurbished listings from across the web
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {secondhand.map((sh, i) => (
                      <div key={i} className="bg-gray-900 border border-amber-900/30 rounded-2xl overflow-hidden hover:border-amber-600/50 transition">
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
      </main>
    </div>
  )
}

function delay(ms: number) { return new Promise(r => setTimeout(r, ms)) }
