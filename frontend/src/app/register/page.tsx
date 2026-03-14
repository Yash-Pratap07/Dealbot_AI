'use client'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import SocialAuthButtons from '@/components/SocialAuthButtons'

export default function RegisterPage() {
  const { register } = useAuth()
  const router = useRouter()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      router.push('/dashboard/buyer')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#0f0f1a] flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-1">Create account</h2>
        <p className="text-zinc-400 text-sm mb-6">Join DealBot AI</p>
        {error && <div className="bg-red-900/40 text-red-400 text-sm px-4 py-2 rounded-lg mb-4">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          {[
            { key: 'username', label: 'Username', type: 'text' },
            { key: 'email', label: 'Email', type: 'email' },
            { key: 'password', label: 'Password', type: 'password' },
          ].map(({ key, label, type }) => (
            <div key={key}>
              <label className="text-xs text-zinc-400 block mb-1">{label}</label>
              <input
                type={type}
                className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500"
                value={(form as any)[key]}
                onChange={e => setForm({ ...form, [key]: e.target.value })}
                required
              />
            </div>
          ))}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold disabled:opacity-50 mt-2"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <SocialAuthButtons onError={setError} />

        <p className="text-center text-zinc-500 text-sm mt-5">
          Already have an account?{' '}
          <Link href="/login" className="text-violet-400 hover:underline">Login</Link>
        </p>
      </div>
    </main>
  )
}

