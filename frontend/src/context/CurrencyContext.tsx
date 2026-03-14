'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

// ── Supported Currencies ──────────────────────────────────────────────────────

export interface CurrencyInfo {
  code: string
  symbol: string
  label: string
  flag: string
}

export const CURRENCIES: CurrencyInfo[] = [
  { code: 'INR', symbol: '₹',    label: 'Indian Rupee',     flag: '🇮🇳' },
  { code: 'USD', symbol: '$',    label: 'US Dollar',        flag: '🇺🇸' },
  { code: 'EUR', symbol: '€',    label: 'Euro',             flag: '🇪🇺' },
  { code: 'GBP', symbol: '£',    label: 'British Pound',    flag: '🇬🇧' },
  { code: 'JPY', symbol: '¥',    label: 'Japanese Yen',     flag: '🇯🇵' },
  { code: 'AED', symbol: 'د.إ',  label: 'UAE Dirham',       flag: '🇦🇪' },
  { code: 'CAD', symbol: 'C$',   label: 'Canadian Dollar',  flag: '🇨🇦' },
  { code: 'AUD', symbol: 'A$',   label: 'Australian Dollar', flag: '🇦🇺' },
  { code: 'SGD', symbol: 'S$',   label: 'Singapore Dollar', flag: '🇸🇬' },
  { code: 'CHF', symbol: 'Fr',   label: 'Swiss Franc',      flag: '🇨🇭' },
]

// ── FX Rates (to INR) — mirrors backend pipeline.py _FX_TO_INR ───────────────

const FX_TO_INR: Record<string, number> = {
  INR: 1.0,
  USD: 83.5,
  EUR: 91.0,
  GBP: 106.0,
  JPY: 0.56,
  AED: 22.73,
  CAD: 61.5,
  AUD: 54.8,
  SGD: 62.3,
  CHF: 94.5,
}

function convertCurrency(amount: number, from: string, to: string): number {
  if (from === to) return amount
  const inr = amount * (FX_TO_INR[from] ?? 83.5)
  const toRate = FX_TO_INR[to] ?? 1.0
  return Math.round((inr / toRate) * 100) / 100
}

// ── Context ───────────────────────────────────────────────────────────────────

interface CurrencyContextType {
  currency: string
  currencyInfo: CurrencyInfo
  setCurrency: (code: string) => void
  currSymbol: string
  formatPrice: (amount: number, sourceCurrency?: string) => string
  convertPrice: (amount: number, sourceCurrency?: string) => number
}

const CurrencyContext = createContext<CurrencyContextType | null>(null)

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState('INR')

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('dealbot_currency')
    if (saved && CURRENCIES.some(c => c.code === saved)) {
      setCurrencyState(saved)
    }
  }, [])

  const setCurrency = (code: string) => {
    setCurrencyState(code)
    localStorage.setItem('dealbot_currency', code)
  }

  const currencyInfo = CURRENCIES.find(c => c.code === currency) ?? CURRENCIES[0]
  const currSymbol = currencyInfo.symbol

  const convertPrice = (amount: number, sourceCurrency?: string): number => {
    const from = sourceCurrency ?? 'INR'
    return convertCurrency(amount, from, currency)
  }

  const formatPrice = (amount: number, sourceCurrency?: string): string => {
    const converted = convertPrice(amount, sourceCurrency)
    const locale = currency === 'INR' ? 'en-IN' : 'en-US'
    return `${currSymbol}${converted.toLocaleString(locale, { maximumFractionDigits: 2 })}`
  }

  return (
    <CurrencyContext.Provider value={{ currency, currencyInfo, setCurrency, currSymbol, formatPrice, convertPrice }}>
      {children}
    </CurrencyContext.Provider>
  )
}

export function useCurrency() {
  const ctx = useContext(CurrencyContext)
  if (!ctx) throw new Error('useCurrency must be used inside CurrencyProvider')
  return ctx
}
