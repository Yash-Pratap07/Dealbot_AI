// ─── Message Types ────────────────────────────────────────────────────────────

export type RoundMessage = {
  type: 'round'
  round: number
  buyer: number
  seller: number
  buyer_message: string
  seller_message: string
  gap: number
  strategy: string
  buyer_model: string
  seller_model: string
  fraud_flag: string | null
}

export type VoteResult = {
  model: string
  vote: 'ACCEPT' | 'REJECT'
  confidence: number
  reasoning: string
}

export type VotingResult = {
  votes: VoteResult[]
  decision: 'ACCEPT' | 'REJECT'
  accept_count: number
  reject_count: number
}

export type EvaluationResult = {
  verdict: 'ACCEPT' | 'NEGOTIATE'
  confidence: number
  deviation: number
  market_price: number
  fair_range: [number, number]
  message: string
}

export type DoneMessage = {
  type: 'done'
  agreement: boolean
  final_price?: number
  contract_hash?: string
  history: RoundMessage[]
  evaluation?: EvaluationResult
  votes?: VotingResult
  fraud_flags?: string[]
  rounds_taken?: number
  strategy_switched?: boolean
  memory_hint?: { has_memory: boolean; avg_accepted_price?: number }
}

export type WSMessage = RoundMessage | DoneMessage

export type Strategy = 'aggressive' | 'balanced' | 'conservative'

export interface NegotiationOptions {
  max_price: number
  min_price: number
  buyer_model?: string
  seller_model?: string
  strategy?: Strategy
  product?: string
  market_price?: number | null
}

// ─── Connection helper ────────────────────────────────────────────────────────

export const connectNegotiation = (
  options: NegotiationOptions,
  onMessage: (data: WSMessage) => void,
  onError?: (e: Event) => void
): WebSocket => {
  const ws = new WebSocket('ws://localhost:8000/ws/negotiate')

  ws.onopen = () => {
    // Include JWT token so backend can save deals to user's history
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    ws.send(JSON.stringify({
      max_price:    options.max_price,
      min_price:    options.min_price,
      buyer_model:  options.buyer_model  ?? 'gemini',
      seller_model: options.seller_model ?? 'gemini',
      strategy:     options.strategy     ?? 'balanced',
      product:      options.product      ?? 'item',
      market_price: options.market_price ?? null,
      token:        token ?? undefined,
    }))
  }

  ws.onmessage = (event) => {
    const data: WSMessage = JSON.parse(event.data)
    onMessage(data)
  }

  ws.onerror = (e) => onError?.(e)

  return ws
}
