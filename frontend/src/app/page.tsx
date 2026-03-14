'use client'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function Home() {
  const { user } = useAuth()
  const router = useRouter()
  useEffect(() => { if (user) router.push('/dashboard/buyer') }, [user, router])
  return (
    <main className="min-h-screen bg-[#0f0f1a] flex flex-col items-center justify-center px-4 text-white">
      <h1 className="text-5xl font-bold bg-gradient-to-r from-violet-500 to-blue-500 bg-clip-text text-transparent mb-4">
        🤖 DealBot AI
      </h1>
      <p className="text-zinc-400 text-lg mb-10 text-center max-w-md">
        Multi-agent AI price negotiation with real-time WebSocket, JWT auth &amp; blockchain contracts
      </p>
      <div className="flex gap-4">
        <Link href="/login" className="px-8 py-3 rounded-xl bg-violet-600 hover:bg-violet-700 font-semibold transition">Login</Link>
        <Link href="/register" className="px-8 py-3 rounded-xl border border-violet-500 hover:bg-violet-900/30 font-semibold transition">Register</Link>
      </div>
    </main>
  )
}
