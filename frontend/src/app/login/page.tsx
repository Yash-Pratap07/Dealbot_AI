'use client'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import SocialAuthButtons from '@/components/SocialAuthButtons'

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      router.push('/dashboard/buyer')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#0f0f1a] flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-1">Welcome back</h2>
        <p className="text-zinc-400 text-sm mb-6">Log in to DealBot AI</p>
        {error && <div className="bg-red-900/40 text-red-400 text-sm px-4 py-2 rounded-lg mb-4">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Username</label>
            <input
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500"
              value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Password</label>
            <input
              type="password"
              className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold disabled:opacity-50 mt-2"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <SocialAuthButtons onError={setError} />

        <p className="text-center text-zinc-500 text-sm mt-5">
          No account?{' '}
          <Link href="/register" className="text-violet-400 hover:underline">Register</Link>
        </p>
      </div>
    </main>
  )
}

