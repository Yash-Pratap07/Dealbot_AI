'use client'
import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'

/**
 * Inner component — needs Suspense because it calls useSearchParams().
 */
function AuthCompleteInner() {
  const router = useRouter()
  const params = useSearchParams()
  const { loginWithToken } = useAuth()
  const [status, setStatus] = useState('Signing you in…')

  useEffect(() => {
    const token = params.get('token')
    const error = params.get('error')

    if (error || !token) {
      router.replace(`/login?error=${encodeURIComponent(error || 'unknown')}`)
      return
    }

    // Call loginWithToken which stores token AND fetches /auth/me to set user state
    // Only redirect AFTER AuthContext state is fully updated
    loginWithToken(token)
      .then(() => {
        setStatus('Redirecting…')
        router.replace('/dashboard/buyer')
      })
      .catch(() => {
        router.replace('/login?error=token_invalid')
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
      <p className="text-gray-400 animate-pulse">{status}</p>
    </div>
  )
}

export default function AuthCompletePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
        <p className="text-gray-400 animate-pulse">Loading…</p>
      </div>
    }>
      <AuthCompleteInner />
    </Suspense>
  )
}
