'use client'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useCurrency, CURRENCIES } from '@/context/CurrencyContext'
import { useRouter } from 'next/navigation'
import { ArrowRightOnRectangleIcon, UserCircleIcon } from '@heroicons/react/24/outline'

export default function Topbar({ title }: { title: string }) {
  const { user, logout } = useAuth()
  const { currency, setCurrency, currencyInfo } = useCurrency()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const dropRef = useRef<HTMLDivElement>(null)

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <header className="h-14 bg-[#12121f] border-b border-[#2a2a45] flex items-center justify-between px-6 shrink-0">
      <h1 className="text-white font-semibold text-base">{title}</h1>
      <div className="flex items-center gap-3">

        {/* ── Currency Switcher ── */}
        <div className="relative" ref={dropRef}>
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#2a2a45] bg-[#1a1a2e] hover:border-violet-500/50 transition text-sm"
          >
            <span>{currencyInfo.flag}</span>
            <span className="text-white font-semibold text-xs">{currency}</span>
            <span className="text-zinc-500 text-[10px]">{currencyInfo.symbol}</span>
            <svg className={`w-3 h-3 text-zinc-500 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {open && (
            <div className="absolute right-0 top-full mt-1 w-52 bg-[#1a1a2e] border border-[#2a2a45] rounded-xl shadow-xl shadow-black/40 z-50 py-1 max-h-80 overflow-y-auto">
              <div className="px-3 py-2 text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">Currency</div>
              {CURRENCIES.map(c => (
                <button
                  key={c.code}
                  onClick={() => { setCurrency(c.code); setOpen(false) }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm transition hover:bg-violet-600/20 ${
                    currency === c.code ? 'bg-violet-600/10 text-white' : 'text-zinc-400'
                  }`}
                >
                  <span className="text-base">{c.flag}</span>
                  <span className="font-medium">{c.code}</span>
                  <span className="text-zinc-500 text-xs">{c.symbol}</span>
                  <span className="text-zinc-600 text-xs ml-auto">{c.label}</span>
                  {currency === c.code && <span className="text-violet-400 text-xs">✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 text-zinc-400 text-sm">
          <UserCircleIcon className="w-5 h-5" />
          <span>{user?.username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-red-400 transition px-2 py-1 rounded-lg hover:bg-red-500/10"
        >
          <ArrowRightOnRectangleIcon className="w-4 h-4" />
          Logout
        </button>
      </div>
    </header>
  )
}
