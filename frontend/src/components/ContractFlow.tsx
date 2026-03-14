'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

declare global { interface Window { ethereum?: any } }

interface Round { round: number; buyer: number; seller: number }

export interface DealResult {
  finalPrice:   number
  agreement:    boolean
  contractHash: string
  rounds:       Round[]
}

interface Props { deal: DealResult | null }

type StepId = 'deal' | 'approval' | 'contract' | 'hashing' | 'deploy' | 'transfer'

const STEPS: { id: StepId; label: string; icon: string }[] = [
  { id: 'deal',     label: 'Deal Reached',          icon: '🤝' },
  { id: 'approval', label: 'Human Approval',         icon: '👤' },
  { id: 'contract', label: 'Generate Contract JSON', icon: '📄' },
  { id: 'hashing',  label: 'Hash Transcript',        icon: '🔐' },
  { id: 'deploy',   label: 'Deploy Smart Contract',  icon: '⛓️'  },
  { id: 'transfer', label: 'Transfer WUSD',          icon: '💸' },
]

async function sha256hex(data: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(data))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

function fakeTx(): string {
  return '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join('')
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)) }

export default function ContractFlow({ deal }: Props) {
  const [activeStep,     setActiveStep]     = useState(0)
  const [contractJson,   setContractJson]   = useState<string | null>(null)
  const [transcriptHash, setTranscriptHash] = useState<string | null>(null)
  const [deployTx,       setDeployTx]       = useState<string | null>(null)
  const [transferTx,     setTransferTx]     = useState<string | null>(null)
  const [loading,        setLoading]        = useState(false)
  const [error,          setError]          = useState('')
  const [copied,         setCopied]         = useState<string | null>(null)

  useEffect(() => {
    if (!deal) return
    setActiveStep(0)
    setContractJson(null)
    setTranscriptHash(null)
    setDeployTx(null)
    setTransferTx(null)
    setError('')
    const t = setTimeout(() => setActiveStep(1), 200)
    return () => clearTimeout(t)
  }, [deal?.contractHash])

  useEffect(() => {
    if (activeStep !== 1) return
    const t = setTimeout(() => setActiveStep(2), 1200)
    return () => clearTimeout(t)
  }, [activeStep])

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 1500)
  }

  const approve = () => setActiveStep(3)
  const reject  = () => setActiveStep(-1)

  const generateContract = () => {
    if (!deal) return
    const json = {
      version:      '1.0',
      timestamp:    new Date().toISOString(),
      parties:      { buyer: 'Buyer Agent', seller: 'Seller Agent' },
      finalPrice:   deal.finalPrice,
      currency:     'WUSD',
      agreement:    deal.agreement,
      rounds:       deal.rounds.length,
      contractHash: deal.contractHash,
    }
    setContractJson(JSON.stringify(json, null, 2))
    setActiveStep(4)
  }

  const hashTranscript = async () => {
    setLoading(true); setError('')
    try {
      const hex = await sha256hex(JSON.stringify(deal?.rounds ?? []))
      setTranscriptHash(hex)
      setActiveStep(5)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const deployContract = async () => {
    setLoading(true); setError('')
    try {
      const REGISTRY_ADDRESS = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS ?? ''
      const hasMetaMask = typeof window !== 'undefined' && !!window.ethereum
      const hasAddress  = !!REGISTRY_ADDRESS
      if (hasMetaMask && hasAddress) {
        const { ethers } = await import('ethers')
        const ABI = ['function recordDeal(string calldata dealHash, uint256 finalPriceCents, bool agreement) external returns (uint256)']
        const provider = new ethers.BrowserProvider(window.ethereum)
        const signer   = await provider.getSigner()
        const registry = new ethers.Contract(REGISTRY_ADDRESS, ABI, signer)
        const priceCents = Math.round((deal?.finalPrice ?? 0) * 100)
        const tx = await registry.recordDeal(transcriptHash ?? '', priceCents, deal?.agreement ?? false)
        await tx.wait()
        setDeployTx(tx.hash)
      } else {
        await sleep(2000)
        setDeployTx(fakeTx())
      }
      setActiveStep(6)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const transferWUSD = async () => {
    setLoading(true); setError('')
    try {
      const WUSD_ADDRESS = process.env.NEXT_PUBLIC_WUSD_ADDRESS ?? ''
      const hasMetaMask = typeof window !== 'undefined' && !!window.ethereum
      const hasAddress  = !!WUSD_ADDRESS
      if (hasMetaMask && hasAddress) {
        const { ethers } = await import('ethers')
        const ABI = ['function transfer(address to, uint256 amount) returns (bool)']
        const provider = new ethers.BrowserProvider(window.ethereum)
        const signer   = await provider.getSigner()
        const token  = new ethers.Contract(WUSD_ADDRESS, ABI, signer)
        const amount = ethers.parseUnits(String(deal?.finalPrice ?? 0), 18)
        const tx     = await token.transfer(await signer.getAddress(), amount)
        await tx.wait()
        setTransferTx(tx.hash)
      } else {
        await sleep(2200)
        setTransferTx(fakeTx())
      }
      setActiveStep(7)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col gap-4">

      {/* Deal Terms */}
      <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">Deal Terms</h3>
        {deal ? (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-zinc-500">Status</span>
              <span className={deal.agreement ? 'text-green-400 font-semibold' : 'text-red-400'}>
                {deal.agreement ? '✅ Agreed' : '❌ No Deal'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Final Price</span>
              <span className="text-white font-bold">₹{deal.finalPrice.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Rounds</span>
              <span className="text-zinc-300">{deal.rounds.length}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-800">
              <p className="text-zinc-500 text-xs mb-0.5">Contract Hash</p>
              <p className="text-xs font-mono text-violet-400 break-all leading-relaxed">{deal.contractHash}</p>
            </div>
          </div>
        ) : (
          <p className="text-zinc-600 text-sm">Waiting for negotiation to complete…</p>
        )}
      </div>

      {/* Stepper */}
      <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">Contract Pipeline</h3>

        {activeStep === -1 && (
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
            className="text-red-400 text-sm bg-red-950/40 border border-red-800/40 rounded-xl p-3 mb-3">
            ❌ Contract rejected.
            <button onClick={() => setActiveStep(2)} className="ml-3 text-xs underline text-red-300 hover:text-white">Undo</button>
          </motion.div>
        )}

        <div className="space-y-2">
          {STEPS.map((s, i) => {
            const idx      = i + 1
            const isDone   = activeStep > idx
            const isActive = activeStep === idx

            return (
              <motion.div key={s.id}
                initial={{ opacity: 0.35 }}
                animate={{ opacity: activeStep >= idx ? 1 : 0.35 }}
                transition={{ duration: 0.3 }}
                className={`rounded-xl border p-3 transition-colors ${
                  isDone   ? 'border-green-700/40 bg-green-950/20' :
                  isActive ? 'border-violet-600/60 bg-violet-950/30' :
                             'border-gray-800 bg-gray-900/40'}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg w-7 text-center flex-shrink-0">
                    {isDone ? '✅' : isActive && loading ? '⏳' : s.icon}
                  </span>
                  <span className={`text-sm font-medium flex-1 ${isDone ? 'text-green-400' : isActive ? 'text-white' : 'text-zinc-500'}`}>
                    {s.label}
                  </span>
                  {isDone    && <span className="text-xs text-green-500 font-semibold">done</span>}
                  {isActive  && !loading && <span className="text-xs text-violet-400 animate-pulse">active</span>}
                  {isActive  && loading  && <span className="text-xs text-yellow-400 animate-pulse">processing…</span>}
                </div>

                <AnimatePresence>
                  {isActive && s.id === 'approval' && (
                    <motion.div key="approval-btns"
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="mt-3 flex gap-2 overflow-hidden">
                      <button onClick={approve} className="flex-1 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition">
                        ✔ Approve Deal
                      </button>
                      <button onClick={reject} className="flex-1 py-2 rounded-lg bg-red-700/70 hover:bg-red-600 text-white text-sm transition">
                        ✗ Reject
                      </button>
                    </motion.div>
                  )}

                  {isActive && s.id === 'contract' && (
                    <motion.div key="contract-btn"
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="mt-3 overflow-hidden">
                      <button onClick={generateContract} className="w-full py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold transition">
                        📄 Generate Contract JSON
                      </button>
                    </motion.div>
                  )}
                  {isDone && s.id === 'contract' && contractJson && (
                    <motion.div key="contract-json" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-2 overflow-hidden">
                      <pre className="text-xs text-green-300 bg-black/40 rounded-lg p-3 overflow-x-auto max-h-28 font-mono">{contractJson}</pre>
                      <button onClick={() => copy(contractJson, 'json')} className="mt-1 text-xs text-zinc-500 hover:text-white transition">
                        {copied === 'json' ? '✅ Copied' : '📋 Copy JSON'}
                      </button>
                    </motion.div>
                  )}

                  {isActive && s.id === 'hashing' && (
                    <motion.div key="hash-btn"
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="mt-3 overflow-hidden">
                      <button onClick={hashTranscript} disabled={loading} className="w-full py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white text-sm font-semibold transition">
                        {loading ? '⏳ Hashing…' : '🔐 Hash Transcript (SHA-256)'}
                      </button>
                    </motion.div>
                  )}
                  {isDone && s.id === 'hashing' && transcriptHash && (
                    <motion.div key="hash-val" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-2 overflow-hidden">
                      <p className="text-xs text-green-400 font-mono break-all bg-black/40 rounded-lg px-3 py-2">{transcriptHash}</p>
                      <button onClick={() => copy(transcriptHash, 'hash')} className="mt-1 text-xs text-zinc-500 hover:text-white transition">
                        {copied === 'hash' ? '✅ Copied' : '📋 Copy Hash'}
                      </button>
                    </motion.div>
                  )}

                  {isActive && s.id === 'deploy' && (
                    <motion.div key="deploy-btn"
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="mt-3 overflow-hidden">
                      <button onClick={deployContract} disabled={loading} className="w-full py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white text-sm font-semibold transition">
                        {loading ? '⏳ Deploying…' : '⛓️ Deploy to Blockchain'}
                      </button>
                      <p className="mt-1.5 text-xs text-yellow-600">⚠ No contract set — runs in simulation mode</p>
                    </motion.div>
                  )}
                  {isDone && s.id === 'deploy' && deployTx && (
                    <motion.div key="deploy-tx" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-2 overflow-hidden">
                      <p className="text-xs text-zinc-500 mb-0.5">Tx Hash</p>
                      <p className="text-xs text-violet-400 font-mono break-all">{deployTx}</p>
                      <button onClick={() => copy(deployTx, 'deploy')} className="mt-1 text-xs text-zinc-500 hover:text-white transition">
                        {copied === 'deploy' ? '✅ Copied' : '📋 Copy Tx'}
                      </button>
                    </motion.div>
                  )}

                  {isActive && s.id === 'transfer' && (
                    <motion.div key="transfer-btn"
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="mt-3 overflow-hidden">
                      <div className="mb-2 text-xs text-zinc-400 bg-zinc-800/50 rounded-lg px-3 py-2">
                        Amount: <span className="text-white font-semibold">₹{deal?.finalPrice.toFixed(2)} WUSD</span>
                      </div>
                      <button onClick={transferWUSD} disabled={loading} className="w-full py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-60 text-white text-sm font-semibold transition">
                        {loading ? '⏳ Transferring…' : '💸 Transfer WUSD'}
                      </button>
                      <p className="mt-1.5 text-xs text-yellow-600">⚠ No WUSD address set — runs in simulation mode</p>
                    </motion.div>
                  )}
                  {isDone && s.id === 'transfer' && transferTx && (
                    <motion.div key="transfer-tx" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-2 overflow-hidden">
                      <p className="text-xs text-zinc-500 mb-0.5">Transfer Tx</p>
                      <p className="text-xs text-green-400 font-mono break-all">{transferTx}</p>
                      <button onClick={() => copy(transferTx, 'transfer')} className="mt-1 text-xs text-zinc-500 hover:text-white transition">
                        {copied === 'transfer' ? '✅ Copied' : '📋 Copy Tx'}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="mt-3 text-xs text-red-400 bg-red-950/40 border border-red-800/40 rounded-xl p-3 break-words flex gap-2">
            <span>⚠️</span>
            <div className="flex-1">
              {error}
              <button onClick={() => setError('')} className="ml-2 underline text-red-300 hover:text-white">dismiss</button>
            </div>
          </motion.div>
        )}

        {activeStep === 7 && (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="mt-4 rounded-xl border border-green-600/40 bg-green-950/30 p-4 text-center">
            <div className="text-2xl mb-1">🎉</div>
            <p className="text-green-400 font-bold text-sm">Deal Complete!</p>
            <p className="text-zinc-500 text-xs mt-1">Contract deployed &amp; WUSD transferred successfully.</p>
          </motion.div>
        )}
      </div>

      {(transcriptHash || deployTx || transferTx) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Blockchain Audit Trail</h3>
          <div className="space-y-3 text-xs">
            {transcriptHash && (
              <div>
                <p className="text-zinc-500 mb-0.5">🔐 Transcript SHA-256</p>
                <p className="text-violet-400 font-mono break-all">{transcriptHash}</p>
              </div>
            )}
            {deployTx && (
              <div>
                <p className="text-zinc-500 mb-0.5">⛓️ Registry Tx</p>
                <p className="text-blue-400 font-mono break-all">{deployTx}</p>
              </div>
            )}
            {transferTx && (
              <div>
                <p className="text-zinc-500 mb-0.5">💸 WUSD Transfer Tx</p>
                <p className="text-green-400 font-mono break-all">{transferTx}</p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      <div className="bg-gray-900 rounded-2xl p-4 border border-gray-800">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Why Blockchain?</h3>
        <div className="space-y-2">
          {[
            { color: 'text-green-400',  title: '✅ Transparency',        body: 'Every deal is recorded on-chain — anyone can verify the outcome without trusting a central server.' },
            { color: 'text-blue-400',   title: '✅ Tamper-Proof History', body: 'The negotiation transcript is SHA-256 hashed and stored immutably — no party can alter past terms.' },
            { color: 'text-violet-400', title: '✅ Automated Payment',    body: 'WUSD transfers execute automatically via smart contract — no middlemen, no delays.' },
          ].map(item => (
            <div key={item.title} className="flex items-start gap-2.5">
              <div>
                <p className={`text-xs font-semibold ${item.color}`}>{item.title}</p>
                <p className="text-[11px] text-zinc-500 leading-relaxed">{item.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
