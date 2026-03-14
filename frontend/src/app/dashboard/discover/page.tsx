'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency } from '@/context/CurrencyContext'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Product {
  id: string; name: string; category: string; description: string; emoji: string; tags: string[]
}
interface Listing {
  listing_id: string; product: Product; seller_name: string; price: number; currency: string
  condition: string; location: string; stock: number; rating: number; review_count: number
  reviews: string[]; response_time: string; verified: boolean; trust_score: number
  rank_score: number; price_percentile: number
  cheaper_than_original?: boolean; savings?: number; url?: string
}
interface PriceSummary {
  product_id: string; min_price: number; max_price: number; avg_price: number
  spread_pct: number; listing_count: number; savings_vs_max: number
}
interface PipelineResult {
  query: string; products_found: number; listings_found: number
  products: Product[]; listings: Listing[]
  price_summary: Record<string, PriceSummary>
  pipeline_stages: { id: number; name: string; status: string; count: number }[]
  cheaper_count?: number; platform_price?: number; max_savings?: number
  assistant_context?: { original_query: string; parsed: ParsedQuery; preferences: Record<string, string> }
}
interface ParsedQuery {
  original: string; category: string; budget: number | null; currency: string
  search_terms: string; has_preferences: boolean
  preference_questions: PrefQuestion[]
}
interface PrefQuestion { id: string; label: string; emoji: string; options: string[] }
interface ExtractedProduct {
  name: string; emoji: string; category: string; description: string
  platform: { id: string; name: string; icon: string; currency: string }
  platform_price: number; currency: string; original_url: string; asin: string | null
  specs: { key: string; value: string }[]
}

// ─── Constants ────────────────────────────────────────────────────────────────

type TabId = 'assistant' | 'link' | 'search'
type AssistStep = 'query' | 'prefs' | 'results'
type LinkStep  = 'input' | 'analyzing' | 'results'

const TABS: { id: TabId; label: string; icon: string; hint: string }[] = [
  { id: 'assistant', label: 'AI Assistant',  icon: '🤖', hint: 'Describe what you need' },
  { id: 'link',      label: 'Link Analysis', icon: '🔗', hint: 'Paste any product URL'  },
  { id: 'search',    label: 'Quick Search',  icon: '🔍', hint: 'Search directly'        },
]

const PIPELINE_STEPS = [
  { id: 0, label: 'User Query',                     icon: '🧑',  color: 'violet' },
  { id: 1, label: 'Product Discovery Engine',       icon: '🔍',  color: 'blue'   },
  { id: 2, label: 'Price Comparison Engine',        icon: '💰',  color: 'cyan'   },
  { id: 3, label: 'Seller Trust & Review Analyzer', icon: '🛡️',  color: 'green'  },
  { id: 4, label: 'AI Ranking Engine',              icon: '🤖',  color: 'yellow' },
  { id: 5, label: 'Human Selection',                icon: '👆',  color: 'orange' },
  { id: 6, label: 'Negotiation Engine',             icon: '🤝',  color: 'pink'   },
  { id: 7, label: 'Contract Generator',             icon: '📄',  color: 'purple' },
  { id: 8, label: 'Blockchain Storage',             icon: '⛓️',  color: 'indigo' },
  { id: 9, label: 'Payment System',                 icon: '💳',  color: 'teal'   },
]

const STEP_CLR: Record<string, string> = {
  violet:'border-violet-500 text-violet-300 bg-violet-500/10',
  blue:  'border-blue-500   text-blue-300   bg-blue-500/10',
  cyan:  'border-cyan-500   text-cyan-300   bg-cyan-500/10',
  green: 'border-green-500  text-green-300  bg-green-500/10',
  yellow:'border-yellow-500 text-yellow-300 bg-yellow-500/10',
  orange:'border-orange-500 text-orange-300 bg-orange-500/10',
  pink:  'border-pink-500   text-pink-300   bg-pink-500/10',
  purple:'border-purple-500 text-purple-300 bg-purple-500/10',
  indigo:'border-indigo-500 text-indigo-300 bg-indigo-500/10',
  teal:  'border-teal-500   text-teal-300   bg-teal-500/10',
}
const DOT_CLR: Record<string, string> = {
  violet:'bg-violet-500', blue:'bg-blue-500',   cyan:  'bg-cyan-500',
  green: 'bg-green-500',  yellow:'bg-yellow-500',orange:'bg-orange-500',
  pink:  'bg-pink-500',   purple:'bg-purple-500',indigo:'bg-indigo-500',
  teal:  'bg-teal-500',
}

const EXAMPLE_QUERIES = [
  'Gaming laptop under ₹90,000',
  'iPhone under $800',
  'Sony noise-cancelling headphones',
  'Best 4K OLED TV 65 inch',
  'Mirrorless camera for beginners',
  'DJI drone for photography',
]
const EXAMPLE_URLS = [
  'https://www.amazon.in/Apple-iPhone-256GB/dp/B0CKDJ5R5Q',
  'https://www.amazon.com/Sony-WH1000XM6/dp/B0D98XAMPLE',
  'https://www.flipkart.com/asus-rog-gaming-laptop/p/itm123456',
]
const ANALYZING_MSGS = [
  '🔍 Fetching product page…',
  '📦 Extracting product data…',
  '🌐 Searching for alternatives across the web…',
  '🤖 Running AI ranking analysis…',
]

// ─── Small helpers ────────────────────────────────────────────────────────────

function StarRating({ rating }: { rating: number }) {
  return (
    <span className="text-yellow-400 text-xs">
      {'★'.repeat(Math.round(rating))}{'☆'.repeat(5 - Math.round(rating))}
      <span className="text-zinc-400 ml-1">{rating.toFixed(1)}</span>
    </span>
  )
}
function TrustBar({ score }: { score: number }) {
  const c = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${c}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-zinc-400 w-8 text-right">{score.toFixed(0)}</span>
    </div>
  )
}
function PriceBar({ pct }: { pct: number }) {
  const c = pct <= 33 ? 'bg-green-500' : pct <= 66 ? 'bg-yellow-500' : 'bg-red-500'
  const lbl = pct <= 33 ? 'Best Price' : pct <= 66 ? 'Mid Range' : 'Premium'
  const lblC = pct <= 33 ? 'text-green-400' : pct <= 66 ? 'text-yellow-400' : 'text-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${c}`} style={{ width: `${pct || 2}%` }} />
      </div>
      <span className={`text-[10px] font-semibold ${lblC}`}>{lbl}</span>
    </div>
  )
}

function ListingCard({
  listing, index, selected, onSelect, onNegotiate, showSavings = false, currSymbol = '₹',
}: {
  listing: Listing; index: number; selected: boolean
  onSelect: () => void; onNegotiate: () => void; showSavings?: boolean; currSymbol?: string
}) {
  return (
    <div
      onClick={onSelect}
      className={`p-4 cursor-pointer transition-all border-b border-gray-800 ${
        selected ? 'bg-violet-950/40 border-l-2 border-l-violet-500' : 'hover:bg-white/2'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* rank */}
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
          index === 0 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
          index === 1 ? 'bg-zinc-400/10 text-zinc-300 border border-zinc-700' :
          index === 2 ? 'bg-orange-800/20 text-orange-400 border border-orange-700/30' :
          'bg-gray-800 text-zinc-500 border border-gray-700'
        }`}>#{index + 1}</div>

        {/* emoji */}
        <div className="w-11 h-11 bg-gray-800 rounded-xl flex items-center justify-center text-2xl shrink-0">
          {listing.product.emoji}
        </div>

        {/* info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div>
              <p className="font-semibold text-white text-sm">{listing.product.name}</p>
              <p className="text-xs text-zinc-500 mt-0.5">
                {listing.product.category} · {listing.condition}
                {listing.verified && <span className="ml-2 text-green-400">✓ Verified</span>}
              </p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-base font-bold text-white">{currSymbol}{listing.price.toFixed(2)}</p>
              {showSavings && listing.savings != null && listing.savings > 0 && (
                <p className="text-[10px] font-semibold text-green-400">SAVE {currSymbol}{listing.savings.toFixed(2)}</p>
              )}
              {showSavings && listing.cheaper_than_original && (
                <span className="text-[10px] px-1.5 py-0.5 bg-green-900/40 text-green-400 border border-green-700/30 rounded">
                  Cheaper!
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 mb-1.5 flex-wrap">
            <span className="text-xs text-zinc-400">🏪 {listing.seller_name}</span>
            <StarRating rating={listing.rating} />
            <span className="text-[10px] text-zinc-500">({listing.review_count.toLocaleString()})</span>
            <span className="text-[10px] text-zinc-500">⚡ {listing.response_time}</span>
            <span className="text-[10px] text-zinc-500">📦 {listing.stock} left</span>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <div><p className="text-[10px] text-zinc-600 mb-0.5">Trust</p><TrustBar score={listing.trust_score} /></div>
            <div><p className="text-[10px] text-zinc-600 mb-0.5">Price</p><PriceBar pct={listing.price_percentile} /></div>
          </div>
        </div>

        {/* AI score + action */}
        <div className="flex flex-col items-center gap-1 shrink-0">
          <div className={`w-12 h-12 rounded-xl border flex flex-col items-center justify-center ${
            listing.rank_score >= 70 ? 'border-green-500/40 bg-green-500/10' :
            listing.rank_score >= 50 ? 'border-yellow-500/40 bg-yellow-500/10' :
            'border-gray-700 bg-gray-800/40'
          }`}>
            <span className="text-[10px] text-zinc-400">AI</span>
            <span className={`font-bold text-sm ${
              listing.rank_score >= 70 ? 'text-green-300' : listing.rank_score >= 50 ? 'text-yellow-300' : 'text-zinc-400'
            }`}>{listing.rank_score.toFixed(0)}</span>
          </div>
          {selected && (
            <div className="flex flex-col gap-1">
              {listing.url && (
                <a
                  href={listing.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={e => e.stopPropagation()}
                  className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 text-zinc-300 rounded-lg font-semibold whitespace-nowrap text-center"
                >
                  🔗 View
                </a>
              )}
              <button
                onClick={e => { e.stopPropagation(); onNegotiate() }}
                className="text-[10px] px-2 py-1 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-semibold whitespace-nowrap"
              >
                🤝 Negotiate
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Pipeline sidebar ─────────────────────────────────────────────────────────

function PipelineSidebar({ activeStep }: { activeStep: number }) {
  return (
    <aside className="w-60 border-r border-gray-800 bg-gray-950 flex flex-col p-3 gap-0.5 overflow-y-auto shrink-0">
      <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-2 px-1">Pipeline Flow</p>
      {PIPELINE_STEPS.map((step, idx) => {
        const done    = activeStep > step.id
        const active  = activeStep === step.id
        const cls = done    ? 'border-zinc-600 text-zinc-300 bg-zinc-800/40'
                  : active  ? STEP_CLR[step.color]
                  : 'border-zinc-800 text-zinc-600 bg-transparent'
        return (
          <div key={step.id} className="flex flex-col items-center">
            <div className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-[11px] font-medium transition-all duration-300 ${cls}`}>
              <span className="text-sm leading-none">{step.icon}</span>
              <span className="flex-1 leading-snug">{step.label}</span>
              {done   && <span className="text-[9px] text-green-400">✓</span>}
              {active && <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${DOT_CLR[step.color]}`} />}
            </div>
            {idx < PIPELINE_STEPS.length - 1 && (
              <div className={`w-px h-2.5 ${done ? 'bg-zinc-600' : 'bg-zinc-800'}`} />
            )}
          </div>
        )
      })}
    </aside>
  )
}

// ─── Results grid (shared by all flows) ──────────────────────────────────────

function ResultsGrid({
  result, selectedId, onSelect, onNegotiate, showSavings = false, currSymbol = '₹',
}: {
  result: PipelineResult; selectedId: string | null
  onSelect: (l: Listing) => void; onNegotiate: (l: Listing) => void; showSavings?: boolean; currSymbol?: string
}) {
  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Products',    value: result.products_found,  icon: '📦' },
          { label: 'Listings',    value: result.listings_found,  icon: '🏪' },
          { label: 'Best Price',  value: `${currSymbol}${Math.min(...result.listings.map(l => l.price)).toFixed(0)}`, icon: '💰' },
          showSavings && result.max_savings != null && result.max_savings > 0
            ? { label: 'Max Saving',  value: `${currSymbol}${result.max_savings.toFixed(0)}`, icon: '🎉' }
            : { label: 'Engines Run', value: result.pipeline_stages.length, icon: '⚙️' },
        ].map((s, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-3">
            <p className="text-zinc-500 text-xs">{s.icon} {s.label}</p>
            <p className="text-white font-bold text-lg mt-0.5">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Listings */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <h3 className="font-semibold text-white text-sm">🤖 AI-Ranked Listings</h3>
          {showSavings && result.cheaper_count != null && (
            <span className="text-xs px-2 py-0.5 bg-green-900/30 text-green-400 border border-green-700/30 rounded-full">
              {result.cheaper_count} cheaper than original
            </span>
          )}
        </div>
        <div>
          {result.listings.map((l, i) => (
            <ListingCard
              key={l.listing_id}
              listing={l} index={i}
              selected={selectedId === l.listing_id}
              onSelect={() => onSelect(l)}
              onNegotiate={() => onNegotiate(l)}
              showSavings={showSavings}
              currSymbol={currSymbol}
            />
          ))}
        </div>
      </div>

      {/* Stage pills */}
      <div className="flex flex-wrap gap-2">
        {result.pipeline_stages.map(s => (
          <div key={s.id} className="flex items-center gap-1.5 px-2.5 py-1 bg-green-900/20 border border-green-700/30 rounded-lg text-xs text-green-400">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {s.name} · {s.count}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DiscoverPage() {
  const router = useRouter()
  const { currSymbol } = useCurrency()

  // Tab
  const [tab, setTab] = useState<TabId>('assistant')

  // Pipeline sidebar step
  const [activeStep, setActiveStep] = useState(-1)

  // Global selected listing
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // ── Flow A: AI Assistant ──
  const [assStep,     setAssStep]     = useState<AssistStep>('query')
  const [queryText,   setQueryText]   = useState('')
  const [parsed,      setParsed]      = useState<ParsedQuery | null>(null)
  const [prefs,       setPrefs]       = useState<Record<string, string>>({})
  const [assResult,   setAssResult]   = useState<PipelineResult | null>(null)
  const [assLoading,  setAssLoading]  = useState(false)

  // ── Flow B: Link Analysis ──
  const [linkUrl,       setLinkUrl]       = useState('')
  const [linkStep,      setLinkStep]      = useState<LinkStep>('input')
  const [analyzingIdx,  setAnalyzingIdx]  = useState(0)
  const [extracted,     setExtracted]     = useState<ExtractedProduct | null>(null)
  const [linkResult,    setLinkResult]    = useState<PipelineResult | null>(null)
  const [detectedPlat,  setDetectedPlat]  = useState<string>('')

  // ── Flow C: Quick Search ──
  const [searchQ,      setSearchQ]      = useState('')
  const [searchResult, setSearchResult] = useState<PipelineResult | null>(null)
  const [searchLoad,   setSearchLoad]   = useState(false)

  const [error, setError] = useState('')

  // ── helpers ──
  const navigate = (l: Listing) =>
    router.push(`/dashboard/buyer?product=${encodeURIComponent(l.product.name)}&max=${l.price}&min=${Math.round(l.price * 0.75 * 100) / 100}`)

  const detectPlatform = (url: string) => {
    const u = url.toLowerCase()
    if (u.includes('amazon.in'))    return '🛒 Amazon India'
    if (u.includes('amazon.com'))   return '🛒 Amazon US'
    if (u.includes('flipkart'))     return '🛍️ Flipkart'
    if (u.includes('ebay'))         return '⚡ eBay'
    if (u.includes('bestbuy'))      return '💻 Best Buy'
    if (u.includes('apple.com'))    return '🍎 Apple Store'
    if (u.includes('myntra'))       return '👔 Myntra'
    if (u.includes('croma'))        return '⚡ Croma'
    if (u.startsWith('http'))       return '🌐 Online Store'
    return ''
  }

  // ── Flow A handlers ──
  const parseQuery = async () => {
    if (!queryText.trim()) return
    setError('');  setAssLoading(true);  setActiveStep(0)
    try {
      const r = await API.post('/pipeline/assistant/parse', { query: queryText })
      setParsed(r.data)
      if (r.data.has_preferences) {
        setAssStep('prefs')
      } else {
        await discoverWithPrefs({})
      }
    } catch { setError('Could not parse your query. Please try again.') }
    finally  { setAssLoading(false) }
  }

  const discoverWithPrefs = async (overridePrefs?: Record<string, string>) => {
    const finalPrefs = overridePrefs ?? prefs
    setAssLoading(true);  setError('')
    for (let i = 1; i <= 4; i++) { setActiveStep(i); await delay(450) }
    try {
      const r = await API.post('/pipeline/assistant/discover', {
        query: queryText, preferences: finalPrefs, limit: 6,
      })
      setAssResult(r.data);  setAssStep('results');  setActiveStep(5)
    } catch { setError('Discovery failed. Please try again.') }
    finally  { setAssLoading(false) }
  }

  // ── Flow B handlers ──
  const analyzeLink = async () => {
    if (!linkUrl.trim()) return
    if (!linkUrl.startsWith('http')) { setError('Please enter a URL starting with http://'); return }
    setError('');  setLinkStep('analyzing')
    for (let i = 0; i < ANALYZING_MSGS.length; i++) {
      setAnalyzingIdx(i);  await delay(900)
    }
    try {
      const r = await API.post('/pipeline/analyze-link', { url: linkUrl, limit: 5 })
      setExtracted(r.data.product);  setLinkResult(r.data.alternatives)
      setLinkStep('results');  setActiveStep(5)
    } catch { setError('Failed to analyze the link.'); setLinkStep('input') }
  }

  // ── Flow C handler ──
  const runSearch = async () => {
    if (!searchQ.trim()) return
    setError('');  setSearchResult(null);  setSearchLoad(true)
    for (let i = 0; i <= 4; i++) { setActiveStep(i); await delay(500) }
    try {
      const r = await API.get('/pipeline/search', { params: { q: searchQ, limit: 6 } })
      setSearchResult(r.data);  setActiveStep(5)
    } catch { setError('Search failed.'); setActiveStep(-1) }
    finally  { setSearchLoad(false) }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#0f0f1a]">
      <Topbar title="🔍 Discover & Shop" />
      <div className="flex flex-1 overflow-hidden">

        {/* ── Pipeline Sidebar ── */}
        <PipelineSidebar activeStep={activeStep} />

        {/* ── Main area ── */}
        <main className="flex-1 overflow-y-auto p-5 space-y-5">

          {/* Tab bar */}
          <div className="flex gap-2">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); setError(''); setSelectedId(null) }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                  tab === t.id
                    ? 'bg-violet-600/20 border-violet-500/60 text-violet-300'
                    : 'border-gray-700 text-zinc-400 hover:border-gray-600 hover:text-white'
                }`}
              >
                <span className="text-base">{t.icon}</span>
                <span>{t.label}</span>
                <span className="text-[10px] text-zinc-600 hidden sm:inline">{t.hint}</span>
              </button>
            ))}
          </div>

          {error && (
            <div className="px-4 py-3 bg-red-950/40 border border-red-700/40 rounded-xl text-red-400 text-sm">{error}</div>
          )}

          {/* ══════════════════ FLOW A: AI ASSISTANT ══════════════════ */}
          {tab === 'assistant' && (
            <>
              {/* STEP 1: Query input */}
              {assStep === 'query' && (
                <div className="space-y-5">
                  <div className="bg-linear-to-br from-violet-950/40 to-blue-950/40 border border-violet-500/20 rounded-2xl p-8 text-center">
                    <p className="text-3xl mb-3">🤖</p>
                    <h2 className="text-2xl font-bold text-white mb-2">What are you looking for today?</h2>
                    <p className="text-zinc-400 text-sm mb-6">Describe it naturally — include your budget, brand preference, or specs.</p>
                    <div className="max-w-xl mx-auto flex gap-2">
                      <input
                        type="text" value={queryText}
                        onChange={e => setQueryText(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && parseQuery()}
                        placeholder='e.g. "I want a gaming laptop under ₹90,000"'
                        className="flex-1 bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-violet-500 transition"
                      />
                      <button onClick={parseQuery} disabled={assLoading || !queryText.trim()}
                        className="px-5 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition whitespace-nowrap flex items-center gap-2">
                        {assLoading
                          ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Parsing…</>
                          : '→ Find Deals'}
                      </button>
                    </div>
                  </div>

                  {/* Example chips */}
                  <div>
                    <p className="text-xs text-zinc-600 mb-2 uppercase tracking-wider">Try an example:</p>
                    <div className="flex flex-wrap gap-2">
                      {EXAMPLE_QUERIES.map(q => (
                        <button key={q} onClick={() => { setQueryText(q) }}
                          className="px-3 py-1.5 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-violet-500/50 rounded-lg text-xs transition">
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: Preference questions */}
              {assStep === 'prefs' && parsed && (
                <div className="space-y-5">
                  {/* Back + context */}
                  <div className="flex items-center gap-3">
                    <button onClick={() => setAssStep('query')}
                      className="text-zinc-400 hover:text-white text-sm flex items-center gap-1 transition">
                      ← Back
                    </button>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-green-900/20 border border-green-700/30 rounded-lg text-xs text-green-400">
                      ✅ Query understood: <span className="font-semibold text-white ml-1">{parsed.original}</span>
                    </div>
                  </div>

                  {/* Category + budget */}
                  <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 flex items-center gap-4">
                    <div className="w-12 h-12 bg-violet-900/30 border border-violet-700/30 rounded-xl flex items-center justify-center text-2xl">🎯</div>
                    <div>
                      <p className="text-white font-semibold capitalize">{parsed.category.replace(/_/g, ' ')}</p>
                      <p className="text-zinc-400 text-sm">
                        {parsed.budget
                          ? `Budget: ${parsed.currency === 'INR' ? '₹' : parsed.currency === 'EUR' ? '€' : '$'}${parsed.budget.toLocaleString()}`
                          : 'No budget specified — searching all price ranges'}
                      </p>
                    </div>
                  </div>

                  {/* Preference questions */}
                  <div className="space-y-4">
                    <p className="text-sm text-zinc-400 font-medium">Refine your search (optional):</p>
                    {parsed.preference_questions.map(q => (
                      <div key={q.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                        <p className="text-sm font-semibold text-zinc-300 mb-3">
                          <span className="mr-2">{q.emoji}</span>{q.label}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {q.options.map(opt => {
                            const active = prefs[q.id] === opt
                            return (
                              <button key={opt}
                                onClick={() => setPrefs(p => ({ ...p, [q.id]: active ? '' : opt }))}
                                className={`px-3 py-1.5 rounded-lg border text-sm transition ${
                                  active
                                    ? 'border-violet-500 bg-violet-900/40 text-white font-semibold'
                                    : 'border-gray-700 text-zinc-400 hover:border-violet-500/50 hover:text-white'
                                }`}>
                                {opt}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>

                  <button onClick={() => discoverWithPrefs()}
                    disabled={assLoading}
                    className="w-full py-3.5 bg-linear-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 disabled:opacity-50 text-white font-bold rounded-xl transition shadow-lg shadow-violet-500/20 flex items-center justify-center gap-2">
                    {assLoading
                      ? <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Running AI Pipeline…</>
                      : '🚀 Find Best Deals'}
                  </button>
                </div>
              )}

              {/* STEP 3: Results */}
              {assStep === 'results' && assResult && (
                <div className="space-y-4">
                  {assResult.assistant_context && (
                    <div className="flex items-center gap-3">
                      <button onClick={() => { setAssStep('query'); setAssResult(null); setSelectedId(null); setActiveStep(-1) }}
                        className="text-zinc-400 hover:text-white text-sm flex items-center gap-1 transition">
                        ← New Search
                      </button>
                      <div className="px-3 py-1.5 bg-violet-900/20 border border-violet-700/30 rounded-lg text-xs text-violet-300">
                        🎯 Results for: <span className="font-semibold">{assResult.assistant_context.original_query}</span>
                      </div>
                    </div>
                  )}
                  <ResultsGrid
                    result={assResult} selectedId={selectedId}
                    onSelect={l => setSelectedId(l.listing_id)}
                    onNegotiate={navigate}
                    currSymbol={currSymbol}
                  />
                </div>
              )}
            </>
          )}

          {/* ══════════════════ FLOW B: LINK ANALYSIS ══════════════════ */}
          {tab === 'link' && (
            <>
              {/* STEP 1: URL input */}
              {linkStep === 'input' && (
                <div className="space-y-5">
                  <div className="bg-linear-to-br from-orange-950/30 to-pink-950/30 border border-orange-500/20 rounded-2xl p-8 text-center">
                    <p className="text-3xl mb-3">🔗</p>
                    <h2 className="text-2xl font-bold text-white mb-2">Paste a Product Link</h2>
                    <p className="text-zinc-400 text-sm mb-6">
                      We&apos;ll extract the product info and find you cheaper alternatives across the web.
                    </p>
                    <div className="max-w-2xl mx-auto space-y-3">
                      <input
                        type="url" value={linkUrl}
                        onChange={e => { setLinkUrl(e.target.value); setDetectedPlat(detectPlatform(e.target.value)) }}
                        placeholder="https://www.amazon.in/product/…"
                        className="w-full bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-orange-500 transition"
                      />
                      {detectedPlat && (
                        <div className="flex items-center gap-2 text-xs text-orange-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
                          Detected: <span className="font-semibold">{detectedPlat}</span>
                        </div>
                      )}
                      <button onClick={analyzeLink} disabled={!linkUrl.trim()}
                        className="w-full py-3 bg-linear-to-r from-orange-600 to-pink-600 hover:from-orange-500 hover:to-pink-500 disabled:opacity-50 text-white font-bold rounded-xl transition shadow-lg shadow-orange-500/20">
                        🔍 Analyze &amp; Find Alternatives
                      </button>
                    </div>
                  </div>

                  {/* Example URLs */}
                  <div>
                    <p className="text-xs text-zinc-600 mb-2 uppercase tracking-wider">Try an example link:</p>
                    <div className="space-y-2">
                      {EXAMPLE_URLS.map(u => (
                        <button key={u} onClick={() => { setLinkUrl(u); setDetectedPlat(detectPlatform(u)) }}
                          className="w-full text-left px-3 py-2 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-orange-500/50 rounded-lg text-xs font-mono transition truncate">
                          {u}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: Analyzing */}
              {linkStep === 'analyzing' && (
                <div className="flex flex-col items-center justify-center py-16 gap-6">
                  <div className="w-16 h-16 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
                  <div className="text-center space-y-2">
                    <p className="text-white font-semibold text-lg">Analyzing Product Link…</p>
                    <div className="space-y-1">
                      {ANALYZING_MSGS.map((msg, i) => (
                        <p key={i} className={`text-sm transition-all ${
                          i < analyzingIdx ? 'text-green-400' :
                          i === analyzingIdx ? 'text-white animate-pulse' : 'text-zinc-700'
                        }`}>
                          {i < analyzingIdx ? '✓' : i === analyzingIdx ? '⟳' : '○'} {msg}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 3: Results */}
              {linkStep === 'results' && extracted && linkResult && (
                <div className="space-y-5">
                  <div className="flex items-center gap-3">
                    <button onClick={() => { setLinkStep('input'); setExtracted(null); setLinkResult(null); setSelectedId(null); setActiveStep(-1) }}
                      className="text-zinc-400 hover:text-white text-sm flex items-center gap-1 transition">
                      ← Analyze Another
                    </button>
                  </div>

                  {/* Original product card */}
                  <div className="bg-linear-to-r from-orange-950/40 to-pink-950/40 border border-orange-500/20 rounded-2xl p-5">
                    <p className="text-xs text-orange-400 uppercase tracking-wider mb-3 font-semibold">
                      {extracted.platform.icon} Original Listing — {extracted.platform.name}
                    </p>
                    <div className="flex items-start gap-4">
                      <div className="w-16 h-16 bg-gray-800 border border-gray-700 rounded-xl flex items-center justify-center text-3xl shrink-0">
                        {extracted.emoji}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-white font-bold text-lg">{extracted.name}</h3>
                        <p className="text-zinc-400 text-sm mt-0.5">{extracted.description}</p>
                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          {extracted.specs.map(s => (
                            <span key={s.key} className="text-xs px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-zinc-400">
                              {s.key}: <span className="text-white">{s.value}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-zinc-500 text-xs">Listed at</p>
                        <p className="text-2xl font-bold text-white">{currSymbol}{extracted.platform_price.toFixed(2)}</p>
                        <p className="text-xs text-zinc-500">{extracted.currency}</p>
                      </div>
                    </div>
                    {(linkResult.max_savings ?? 0) > 0 && (
                      <div className="mt-4 px-4 py-2.5 bg-green-900/30 border border-green-700/30 rounded-xl text-sm text-green-300 font-medium">
                        🎉 We found <strong>{linkResult.cheaper_count}</strong> cheaper alternative{linkResult.cheaper_count !== 1 ? 's' : ''}!
                        Save up to <strong className="text-green-200">{currSymbol}{(linkResult.max_savings ?? 0).toFixed(2)}</strong> vs. the listed price.
                      </div>
                    )}
                  </div>

                  {/* Alternatives */}
                  <ResultsGrid
                    result={linkResult} selectedId={selectedId}
                    onSelect={l => setSelectedId(l.listing_id)}
                    onNegotiate={navigate}
                    showSavings
                    currSymbol={currSymbol}
                  />
                </div>
              )}
            </>
          )}

          {/* ══════════════════ FLOW C: QUICK SEARCH ══════════════════ */}
          {tab === 'search' && (
            <div className="space-y-5">
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                <h2 className="text-sm text-zinc-400 mb-3 font-medium">Search the product catalog directly:</h2>
                <div className="flex gap-3">
                  <input type="text" value={searchQ}
                    onChange={e => setSearchQ(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && runSearch()}
                    placeholder='e.g. "Sony headphones", "MacBook Pro", "RTX 5090"…'
                    className="flex-1 bg-[#1a1a2e] border border-gray-700 rounded-xl px-4 py-3 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-violet-500 transition"
                  />
                  <button onClick={runSearch} disabled={searchLoad || !searchQ.trim()}
                    className="px-6 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition flex items-center gap-2">
                    {searchLoad
                      ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Running…</>
                      : '🚀 Run Pipeline'}
                  </button>
                </div>
              </div>

              {searchLoad && (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center">
                  <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-zinc-300 font-semibold">Running AI Pipeline…</p>
                  <p className="text-zinc-500 text-sm mt-1">
                    {activeStep === 1 ? '🔍 Discovering products…' :
                     activeStep === 2 ? '💰 Comparing prices…' :
                     activeStep === 3 ? '🛡️ Analyzing seller trust…' :
                     '🤖 AI ranking results…'}
                  </p>
                </div>
              )}

              {searchResult && !searchLoad && (
                <ResultsGrid
                  result={searchResult} selectedId={selectedId}
                  onSelect={l => setSelectedId(l.listing_id)}
                  onNegotiate={navigate}
                  currSymbol={currSymbol}
                />
              )}

              {!searchResult && !searchLoad && (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
                  <div className="text-4xl mb-3">🔍</div>
                  <p className="text-zinc-400 text-sm">Type a product name above and hit Enter or click Run Pipeline.</p>
                  <div className="mt-4 flex flex-wrap justify-center gap-2">
                    {['iPhone 16 Pro', 'DJI drone', 'Sony headphones', 'MacBook Pro', 'PlayStation 6'].map(q => (
                      <button key={q} onClick={() => setSearchQ(q)}
                        className="px-3 py-1.5 bg-gray-800 border border-gray-700 text-zinc-400 hover:text-white hover:border-violet-500/50 rounded-lg text-xs transition">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function delay(ms: number) { return new Promise(r => setTimeout(r, ms)) }
