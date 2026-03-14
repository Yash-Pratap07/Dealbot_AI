'use client'
import { useState, useEffect, useCallback } from 'react'
import Topbar from '@/components/Topbar'
import API from '@/lib/api'
import { useCurrency } from '@/context/CurrencyContext'

// ── Types ─────────────────────────────────────────────────────────────────────

interface AgentIdentity {
  type: string
  index: number
  address: string
  role: string
}

interface Settlement {
  wusd_tx_hash: string
  registry_tx_hash: string
  deal_id_onchain: number
  settlement_mode: string
}

interface DealRecord {
  id: number
  product: string
  final_price: number | null
  agreement: boolean
  contract_hash: string | null
  settlement: Settlement | null
  created_at: string
}

interface ChainStatus {
  chain_live: boolean
  network: string
  rpc_configured: boolean
  contract_configured: boolean
  wusd_configured: boolean
  mode: string
  agent_count: number
}

type WalletTab = 'crypto' | 'upi' | 'bank'

// ── Helpers ───────────────────────────────────────────────────────────────────

const shortAddr = (addr: string) =>
  addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : '—'

const shortHash = (h: string) =>
  h ? `${h.slice(0, 10)}…${h.slice(-6)}` : '—'

const AGENT_COLORS: Record<string, string> = {
  buyer_agent:  'from-blue-500 to-cyan-500',
  seller_agent: 'from-green-500 to-emerald-500',
  evaluator:    'from-yellow-500 to-orange-500',
  voter_gpt:    'from-violet-500 to-purple-500',
  voter_claude: 'from-rose-500 to-pink-500',
  voter_gemini: 'from-sky-500 to-indigo-500',
}

const AGENT_ICONS: Record<string, string> = {
  buyer_agent:  '🛒',
  seller_agent: '🏪',
  evaluator:    '⚖️',
  voter_gpt:    '🧠',
  voter_claude: '🤖',
  voter_gemini: '💎',
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function WalletPage() {
  const { currSymbol } = useCurrency()
  const [walletAddress,   setWalletAddress]   = useState<string | null>(null)
  const [walletProvider,  setWalletProvider]  = useState<string>('')
  const [wusdBalance,     setWusdBalance]     = useState<number | null>(null)
  const [agents,          setAgents]          = useState<AgentIdentity[]>([])
  const [deals,           setDeals]           = useState<DealRecord[]>([])
  const [chainStatus,     setChainStatus]     = useState<ChainStatus | null>(null)
  const [settling,        setSettling]        = useState<number | null>(null)
  const [copied,          setCopied]          = useState<string | null>(null)
  const [loading,         setLoading]         = useState(true)
  const [walletTab,       setWalletTab]       = useState<WalletTab>('crypto')
  const [upiId,           setUpiId]           = useState('')
  const [upiSaved,        setUpiSaved]        = useState(false)
  const [showWCQR,        setShowWCQR]        = useState(false)

  // ── Load backend data ──────────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      const [agentsRes, dealsRes, chainRes] = await Promise.all([
        API.get('/agents/identities'),
        API.get('/wallet/deals'),
        API.get('/wallet/chain-status'),
      ])
      setAgents(agentsRes.data.agents || [])
      setDeals(dealsRes.data || [])
      setChainStatus(chainRes.data)
    } catch {/* auth not ready yet */}
    setLoading(false)
  }, [])

  useEffect(() => { loadData() }, [loadData])

  // ── MetaMask connect ───────────────────────────────────────────────────────
  const connectMetaMask = async () => {
    if (!window.ethereum) {
      alert('MetaMask not installed. Please install it from metamask.io or use WalletConnect to connect from your mobile wallet.')
      return
    }
    const accounts: string[] = await window.ethereum.request({ method: 'eth_requestAccounts' })
    const addr = accounts[0]
    setWalletAddress(addr)
    setWalletProvider('MetaMask')
    try {
      const res = await API.get(`/wallet/balance?address=${addr}`)
      setWusdBalance(res.data.balance_wusd)
    } catch { setWusdBalance(0) }
  }

  // ── WalletConnect (Indian exchange wallets - CoinDCX/WazirX/Mudrex) ────────
  const connectWalletConnect = () => {
    // Show QR code — user scans from their mobile wallet app
    setShowWCQR(true)
  }

  // ── Okto Wallet (Indian Web3 by CoinDCX) ──────────────────────────────────
  const connectOkto = () => {
    window.open('https://okto.tech', '_blank')
    alert('Okto Wallet: Download the Okto app from Play Store / App Store, then use WalletConnect to connect.')
  }

  // ── Save UPI ID ────────────────────────────────────────────────────────────
  const saveUpi = () => {
    if (!upiId.includes('@')) { alert('Enter a valid UPI ID (e.g. yourname@upi)'); return }
    setUpiSaved(true)
  }
  const upiQRUrl = (upi: string, amount?: number) =>
    `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(`upi://pay?pa=${upi}&pn=DealBot AI&cu=INR${amount ? '&am=' + amount : ''}`)}`

  // ── Manually settle a deal ─────────────────────────────────────────────────
  const settleDeal = async (dealId: number) => {
    setSettling(dealId)
    try {
      await API.post(`/wallet/settle/${dealId}`, {}, {
        params: walletAddress ? { buyer_address: walletAddress } : {}
      })
      await loadData()
    } catch { /* ignore */ }
    setSettling(null)
  }

  // ── Copy to clipboard ─────────────────────────────────────────────────────
  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 1500)
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col flex-1">
      <Topbar title="Web4 Wallet" />
      <main className="flex-1 overflow-y-auto p-6 space-y-8">

        {/* ── Network Status Banner ── */}
        {chainStatus && (
          <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm ${
            chainStatus.chain_live
              ? 'bg-emerald-950/50 border-emerald-700 text-emerald-300'
              : 'bg-yellow-950/50 border-yellow-700 text-yellow-300'
          }`}>
            <span className={`w-2.5 h-2.5 rounded-full ${chainStatus.chain_live ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'}`} />
            <span className="font-semibold">{chainStatus.network}</span>
            <span className="text-zinc-400">·</span>
            <span>{chainStatus.mode === 'live' ? '🔗 Live Chain' : '🧪 Simulation Mode'}</span>
            <span className="ml-auto text-xs text-zinc-500">{chainStatus.agent_count} AI agents registered</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ── Payment Hub ── */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold flex items-center gap-2">
                <span className="text-xl">💳</span> Payment Hub
              </h2>
              {walletAddress
                ? <span className="text-xs text-emerald-400 bg-emerald-950 px-2 py-1 rounded-full">✓ {walletProvider} Connected</span>
                : upiSaved
                ? <span className="text-xs text-blue-400 bg-blue-950 px-2 py-1 rounded-full">✓ UPI Linked</span>
                : <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-1 rounded-full">Not connected</span>
              }
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-zinc-800 rounded-xl p-1 mb-5">
              {(['crypto', 'upi', 'bank'] as WalletTab[]).map(tab => (
                <button key={tab} onClick={() => setWalletTab(tab)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
                    walletTab === tab
                      ? 'bg-violet-600 text-white'
                      : 'text-zinc-400 hover:text-white'
                  }`}>
                  {tab === 'crypto' && '⛓️ Crypto'}
                  {tab === 'upi'    && '📱 UPI'}
                  {tab === 'bank'   && '🏦 Bank'}
                </button>
              ))}
            </div>

            {/* ── CRYPTO TAB ── */}
            {walletTab === 'crypto' && (
              <div>
                {walletAddress ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 bg-zinc-800 rounded-xl px-4 py-3">
                      <span className="text-zinc-400 text-xs">Address</span>
                      <span className="ml-auto font-mono text-sm text-white">{shortAddr(walletAddress)}</span>
                      <button onClick={() => copy(walletAddress, 'my-addr')} className="text-zinc-500 hover:text-white text-xs ml-1">
                        {copied === 'my-addr' ? '✓' : '⎘'}
                      </button>
                      <button onClick={() => { setWalletAddress(null); setWalletProvider(''); setWusdBalance(null) }}
                        className="text-zinc-600 hover:text-red-400 text-xs ml-1">✕</button>
                    </div>
                    <div className="flex items-center gap-2 bg-zinc-800 rounded-xl px-4 py-3">
                      <span className="text-zinc-400 text-xs">WUSD Balance</span>
                      <span className="ml-auto text-lg font-bold text-white">
                        {wusdBalance !== null ? `${wusdBalance.toLocaleString()} WUSD` : '—'}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-600 text-center">Connected via {walletProvider}</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {/* WalletConnect */}
                    <button onClick={connectWalletConnect}
                      className="flex flex-col items-center gap-2 p-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-violet-500 transition group">
                      <div className="w-12 h-12 rounded-2xl bg-linear-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-2xl">🔗</div>
                      <span className="text-white text-sm font-semibold">WalletConnect</span>
                      <span className="text-zinc-500 text-xs text-center leading-snug">Scan QR from CoinDCX, WazirX, Mudrex, Trust Wallet</span>
                      <span className="text-xs text-blue-400 bg-blue-950 px-2 py-0.5 rounded-full">🇮🇳 Indian exchanges</span>
                    </button>

                    {/* Okto Wallet */}
                    <button onClick={connectOkto}
                      className="flex flex-col items-center gap-2 p-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-emerald-500 transition group">
                      <div className="w-12 h-12 rounded-2xl bg-linear-to-br from-emerald-500 to-teal-400 flex items-center justify-center text-2xl">🪙</div>
                      <span className="text-white text-sm font-semibold">Okto Wallet</span>
                      <span className="text-zinc-500 text-xs text-center leading-snug">Indian Web3 wallet by CoinDCX</span>
                      <span className="text-xs text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded-full">🇮🇳 Made in India</span>
                    </button>

                    {/* MetaMask */}
                    <button onClick={connectMetaMask}
                      className="flex flex-col items-center gap-2 p-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-orange-500 transition group">
                      <div className="w-12 h-12 rounded-2xl bg-linear-to-br from-orange-500 to-amber-400 flex items-center justify-center text-2xl">🦊</div>
                      <span className="text-white text-sm font-semibold">MetaMask</span>
                      <span className="text-zinc-500 text-xs text-center leading-snug">Browser extension wallet</span>
                      <span className="text-xs text-orange-400 bg-orange-950 px-2 py-0.5 rounded-full">Desktop only</span>
                    </button>

                    {/* WalletConnect QR Modal */}
                    {showWCQR && (
                      <div className="sm:col-span-3 flex flex-col items-center gap-3 p-4 bg-zinc-800 rounded-2xl border border-violet-700">
                        <p className="text-white text-sm font-semibold">📷 Scan with your wallet app</p>
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=wc:dealbot-ai-session@2?relay-protocol=irn" alt="WalletConnect QR" className="rounded-xl" />
                        <p className="text-zinc-500 text-xs text-center">Open CoinDCX / WazirX / Mudrex / Trust Wallet → Scan QR → Connect</p>
                        <div className="flex gap-3 flex-wrap justify-center">
                          {[
                            { name: 'CoinDCX',   url: 'https://coindcx.com',    emoji: '🇮🇳' },
                            { name: 'WazirX',    url: 'https://wazirx.com',     emoji: '🇮🇳' },
                            { name: 'Mudrex',    url: 'https://mudrex.com',     emoji: '🇮🇳' },
                            { name: 'Trust',     url: 'https://trustwallet.com',emoji: '🔒' },
                          ].map(w => (
                            <a key={w.name} href={w.url} target="_blank" rel="noreferrer"
                              className="text-xs text-zinc-400 hover:text-white bg-zinc-700 px-2 py-1 rounded-lg">
                              {w.emoji} {w.name}
                            </a>
                          ))}
                        </div>
                        <button onClick={() => setShowWCQR(false)} className="text-xs text-zinc-600 hover:text-white">Close</button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── UPI TAB ── */}
            {walletTab === 'upi' && (
              <div className="space-y-4">
                {upiSaved ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 bg-zinc-800 rounded-xl px-4 py-3">
                      <span className="text-zinc-400 text-xs">UPI ID</span>
                      <span className="ml-auto text-sm text-white font-medium">{upiId}</span>
                      <button onClick={() => copy(upiId, 'upi-id')} className="text-zinc-500 hover:text-white text-xs">
                        {copied === 'upi-id' ? '✓' : '⎘'}
                      </button>
                      <button onClick={() => setUpiSaved(false)} className="text-zinc-600 hover:text-red-400 text-xs ml-1">✕</button>
                    </div>
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-zinc-400 text-xs">Scan to pay via any UPI app</p>
                      <img src={upiQRUrl(upiId)} alt="UPI QR" className="rounded-xl border border-zinc-700" />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { name: 'Google Pay', emoji: 'G', color: 'from-blue-500 to-green-500', url: `gpay://upi/pay?pa=${upiId}&pn=DealBot` },
                        { name: 'PhonePe',    emoji: '📲', color: 'from-violet-600 to-violet-400', url: `phonepe://pay?pa=${upiId}&pn=DealBot` },
                        { name: 'Paytm',      emoji: '💙', color: 'from-sky-500 to-cyan-400',    url: `paytmmp://pay?pa=${upiId}&pn=DealBot` },
                      ].map(app => (
                        <a key={app.name} href={app.url}
                          className={`flex flex-col items-center gap-1.5 p-3 rounded-xl bg-linear-to-br ${app.color} hover:opacity-90 transition`}>
                          <span className="text-xl">{app.emoji}</span>
                          <span className="text-white text-xs font-semibold">{app.name}</span>
                        </a>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-600 text-center">Payments secured via NPCI UPI network</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-zinc-400 text-sm">Link your UPI ID to receive INR payments for deals</p>
                    <div className="flex gap-2">
                      <input
                        value={upiId}
                        onChange={e => setUpiId(e.target.value)}
                        placeholder="yourname@upi (e.g. 9876543210@paytm)"
                        className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500"
                      />
                      <button onClick={saveUpi}
                        className="px-4 py-2.5 rounded-xl bg-linear-to-r from-violet-600 to-blue-600 text-white font-semibold text-sm hover:opacity-90">
                        Link
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {[
                        { label: '@paytm',     hint: 'Paytm UPI',    color: 'bg-sky-900/40 border-sky-800 text-sky-300' },
                        { label: '@ybl',       hint: 'PhonePe',      color: 'bg-violet-900/40 border-violet-800 text-violet-300' },
                        { label: '@okicici',   hint: 'iMobile Pay',  color: 'bg-orange-900/40 border-orange-800 text-orange-300' },
                        { label: '@oksbi',     hint: 'BHIM SBI',     color: 'bg-blue-900/40 border-blue-800 text-blue-300' },
                        { label: '@okhdfcbank',hint: 'HDFC Pay',     color: 'bg-red-900/40 border-red-800 text-red-300' },
                        { label: '@axl',       hint: 'Axis Pay',     color: 'bg-pink-900/40 border-pink-800 text-pink-300' },
                      ].map(h => (
                        <button key={h.label} onClick={() => setUpiId(prev => prev.split('@')[0] + h.label)}
                          className={`text-xs px-3 py-2 rounded-lg border ${h.color} text-left`}>
                          <span className="font-mono font-bold">{h.label}</span>
                          <span className="text-zinc-500 ml-1">— {h.hint}</span>
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-600">Powered by NPCI · Works with all Indian banks</p>
                  </div>
                )}
              </div>
            )}

            {/* ── BANK TAB ── */}
            {walletTab === 'bank' && (
              <div className="space-y-4">
                <p className="text-zinc-400 text-sm">NEFT / IMPS / RTGS bank transfer for deal settlements</p>
                <div className="bg-zinc-800 rounded-2xl p-4 space-y-3">
                  {[
                    { label: 'Bank Name',       value: 'State Bank of India' },
                    { label: 'Account Number',  value: 'XXXX XXXX XXXX' },
                    { label: 'IFSC Code',       value: 'SBIN0000XXX' },
                    { label: 'Account Holder',  value: 'DealBot AI Platform' },
                  ].map(field => (
                    <div key={field.label} className="flex items-center justify-between">
                      <span className="text-zinc-500 text-xs">{field.label}</span>
                      <span className="text-zinc-300 text-sm font-medium font-mono">{field.value}</span>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { name: 'BHIM UPI',  emoji: '🇮🇳', color: 'from-orange-600 to-amber-500' },
                    { name: 'NEFT',      emoji: '🏦', color: 'from-zinc-700 to-zinc-600' },
                    { name: 'IMPS',      emoji: '⚡', color: 'from-zinc-700 to-zinc-600' },
                    { name: 'RTGS',      emoji: '🔄', color: 'from-zinc-700 to-zinc-600' },
                  ].map(m => (
                    <div key={m.name} className={`flex items-center gap-2 px-3 py-2 rounded-xl bg-linear-to-r ${m.color}`}>
                      <span>{m.emoji}</span>
                      <span className="text-white text-sm font-medium">{m.name}</span>
                      <span className="ml-auto text-xs text-white/60">Supported</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-zinc-600">Contact support to set up your bank details for automatic deal settlement</p>
              </div>
            )}
          </div>

          {/* ── Chain Config Status ── */}
          {chainStatus && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
              <h2 className="text-white font-semibold flex items-center gap-2 mb-4">
                <span className="text-xl">⛓️</span> WeilChain Config
              </h2>
              <div className="space-y-2.5">
                {[
                  { label: 'RPC Endpoint',        ok: chainStatus.rpc_configured,      key: 'WEB3_RPC_URL' },
                  { label: 'Smart Contract',       ok: chainStatus.contract_configured, key: 'CONTRACT_ADDRESS' },
                  { label: 'WUSD Token',           ok: chainStatus.wusd_configured,     key: 'WUSD_ADDRESS' },
                  { label: 'Chain Connection',     ok: chainStatus.chain_live,          key: null },
                ].map(item => (
                  <div key={item.label} className="flex items-center gap-3 text-sm">
                    <span className={item.ok ? 'text-emerald-400' : 'text-zinc-600'}>
                      {item.ok ? '✅' : '⬜'}
                    </span>
                    <span className="text-zinc-300">{item.label}</span>
                    {!item.ok && item.key && (
                      <span className="ml-auto font-mono text-xs text-yellow-500 bg-yellow-950/50 px-2 py-0.5 rounded">
                        .env: {item.key}
                      </span>
                    )}
                  </div>
                ))}
              </div>
              {!chainStatus.chain_live && (
                <p className="text-xs text-zinc-500 mt-4 leading-relaxed">
                  Set all 4 env vars in <code className="text-zinc-300">.env</code> and restart the backend to enable live WeilChain settlement.
                </p>
              )}
            </div>
          )}

          {/* ── Web4 Info Panel ── */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <h2 className="text-white font-semibold flex items-center gap-2 mb-4">
              <span className="text-xl">🔐</span> Secure Payments
            </h2>
            <div className="space-y-3">
              {[
                { icon: '🇮🇳', title: 'RBI Compliant', desc: 'UPI powered by NPCI — India\'s national payment infrastructure' },
                { icon: '⛓️', title: 'Blockchain Settled', desc: 'Crypto deals auto-settled on WeilChain via WUSD token' },
                { icon: '🤖', title: 'AI Agents Sign', desc: '6 AI agents sign every deal with cryptographic wallets' },
                { icon: '🔒', title: 'Zero-trust', desc: 'No human intermediary — settlement is fully autonomous' },
              ].map(item => (
                <div key={item.title} className="flex gap-3">
                  <span className="text-xl mt-0.5">{item.icon}</span>
                  <div>
                    <p className="text-white text-sm font-medium">{item.title}</p>
                    <p className="text-zinc-500 text-xs">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── AI Agent Wallets ── */}
        <div>
          <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
            <span className="text-xl">🤖</span> AI Agent Wallets
            <span className="text-xs text-zinc-500 font-normal">– autonomous on-chain identities</span>
          </h2>
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-28 rounded-2xl bg-zinc-800 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {agents.map(agent => (
                <div key={agent.type}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 hover:border-zinc-700 transition">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-xl bg-linear-to-br ${AGENT_COLORS[agent.type] || 'from-zinc-700 to-zinc-600'} flex items-center justify-center text-sm`}>
                        {AGENT_ICONS[agent.type] || '🤖'}
                      </div>
                      <div>
                        <p className="text-white text-xs font-semibold leading-tight">
                          {agent.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </p>
                        <p className="text-zinc-500 text-xs">Agent #{agent.index}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 bg-zinc-800 rounded-lg px-2.5 py-1.5 mt-2">
                    <span className="font-mono text-xs text-zinc-300 flex-1 truncate">{shortAddr(agent.address)}</span>
                    <button onClick={() => copy(agent.address, `agent-${agent.type}`)}
                      className="text-zinc-500 hover:text-white text-xs">
                      {copied === `agent-${agent.type}` ? '✓' : '⎘'}
                    </button>
                  </div>
                  <p className="text-zinc-600 text-xs mt-2 leading-snug line-clamp-2">{agent.role}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Deal Settlements ── */}
        <div>
          <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
            <span className="text-xl">🤝</span> Deal Settlements
            <span className="text-xs text-zinc-500 font-normal">– autonomous WUSD transfers</span>
          </h2>
          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-20 rounded-2xl bg-zinc-800 animate-pulse" />
              ))}
            </div>
          ) : deals.length === 0 ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center">
              <p className="text-zinc-500 text-sm">No deals yet. Start a negotiation to see settlement history.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {deals.map(deal => (
                <div key={deal.id}
                  className={`bg-zinc-900 border rounded-2xl p-4 transition ${
                    deal.agreement ? 'border-zinc-700' : 'border-zinc-800'
                  }`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          deal.agreement
                            ? 'bg-emerald-950 text-emerald-400'
                            : 'bg-zinc-800 text-zinc-500'
                        }`}>
                          {deal.agreement ? '✅ Settled' : '❌ No Deal'}
                        </span>
                        <span className="text-zinc-500 text-xs">{deal.product || 'item'}</span>
                        <span className="ml-auto text-white font-bold text-sm">
                          {deal.final_price ? `${currSymbol}${deal.final_price.toFixed(2)}` : '—'}
                        </span>
                      </div>

                      {deal.settlement && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-2">
                          <div className="flex items-center gap-1.5 bg-zinc-800 rounded-lg px-2.5 py-1.5">
                            <span className="text-zinc-500 text-xs">WUSD TX</span>
                            <span className="font-mono text-xs text-amber-400 ml-auto truncate">
                              {shortHash(deal.settlement.wusd_tx_hash)}
                            </span>
                            <button onClick={() => copy(deal.settlement!.wusd_tx_hash, `wusd-${deal.id}`)}
                              className="text-zinc-600 hover:text-white text-xs shrink-0">
                              {copied === `wusd-${deal.id}` ? '✓' : '⎘'}
                            </button>
                          </div>
                          <div className="flex items-center gap-1.5 bg-zinc-800 rounded-lg px-2.5 py-1.5">
                            <span className="text-zinc-500 text-xs">Registry TX</span>
                            <span className="font-mono text-xs text-violet-400 ml-auto truncate">
                              {shortHash(deal.settlement.registry_tx_hash)}
                            </span>
                            <button onClick={() => copy(deal.settlement!.registry_tx_hash, `reg-${deal.id}`)}
                              className="text-zinc-600 hover:text-white text-xs shrink-0">
                              {copied === `reg-${deal.id}` ? '✓' : '⎘'}
                            </button>
                          </div>
                        </div>
                      )}

                      {deal.contract_hash && (
                        <div className="flex items-center gap-1.5 bg-zinc-800/50 rounded-lg px-2.5 py-1.5 mt-1.5">
                          <span className="text-zinc-600 text-xs">Deal Hash</span>
                          <span className="font-mono text-xs text-zinc-400 ml-auto truncate">
                            {shortHash(deal.contract_hash)}
                          </span>
                        </div>
                      )}
                    </div>

                    {deal.agreement && deal.settlement?.settlement_mode === 'simulated' && !settling && (
                      <button
                        onClick={() => settleDeal(deal.id)}
                        disabled={settling === deal.id}
                        className="shrink-0 text-xs px-3 py-1.5 rounded-lg bg-violet-900/50 border border-violet-700 text-violet-300 hover:bg-violet-900 transition">
                        {settling === deal.id ? '⏳' : '⚡ Live Settle'}
                      </button>
                    )}
                  </div>

                  {deal.settlement && (
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        deal.settlement.settlement_mode === 'live'
                          ? 'bg-emerald-950 text-emerald-400'
                          : 'bg-yellow-950 text-yellow-500'
                      }`}>
                        {deal.settlement.settlement_mode === 'live' ? '🔗 On-chain' : '🧪 Simulated'}
                      </span>
                      {deal.settlement.deal_id_onchain !== undefined && (
                        <span className="text-xs text-zinc-600">Deal #{deal.settlement.deal_id_onchain} on WeilChain</span>
                      )}
                      <span className="text-xs text-zinc-700 ml-auto">
                        {new Date(deal.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </main>
    </div>
  )
}
