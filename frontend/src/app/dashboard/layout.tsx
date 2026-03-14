'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import Sidebar from '@/components/Sidebar'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Wait until AuthContext has finished loading before checking
    if (!loading && user === null) {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      if (!token) router.push('/login')
    }
  }, [user, loading, router])

  // Show nothing while auth is being resolved
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f0f1a] text-white">
        <p className="text-gray-400 animate-pulse">Loading\u2026</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-[#0f0f1a]">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  )
}
