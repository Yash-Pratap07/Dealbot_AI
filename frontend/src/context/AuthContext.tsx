'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import API from '@/lib/api'

interface AuthUser {
  id: number
  username: string
  email: string | null
  phone: string | null
  display_name: string | null
  avatar_url: string | null
  auth_provider: string
}

interface AuthCtx {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login:             (username: string, password: string) => Promise<void>
  register:          (username: string, email: string, password: string) => Promise<void>
  loginWithGoogle:   (credential: string) => Promise<void>
  loginWithFacebook: (accessToken: string) => Promise<void>
  loginWithToken:    (token: string) => Promise<void>
  sendPhoneOTP:      (phone: string) => Promise<void>
  loginWithPhone:    (phone: string, code: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx | null>(null)

// ─── Helper ───────────────────────────────────────────────────────────────────
function storeToken(token: string) {
  localStorage.setItem('token', token)
  API.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]   = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // ── Logout — declared first so useEffect below can reference it ─────────────
  const logout = () => {
    localStorage.removeItem('token')
    delete API.defaults.headers.common['Authorization']
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    const t = localStorage.getItem('token')
    if (t) {
      storeToken(t)
      setToken(t)
      API.get('/auth/me')
        .then(r => setUser(r.data))
        .catch(() => logout())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const _finalize = async (access_token: string) => {
    storeToken(access_token)
    setToken(access_token)
    const me = await API.get('/auth/me')
    setUser(me.data)
  }

  // ── Password login ──────────────────────────────────────────────────────────
  const login = async (username: string, password: string) => {
    const form = new URLSearchParams({ username, password })
    const res = await API.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    await _finalize(res.data.access_token)
  }

  // ── Password register ───────────────────────────────────────────────────────
  const register = async (username: string, email: string, password: string) => {
    const res = await API.post('/auth/register', { username, email, password })
    await _finalize(res.data.access_token)
  }

  // ── Accept a JWT directly (used after redirect-mode Google auth) ─────────────
  const loginWithToken = async (jwt: string) => {
    await _finalize(jwt)
  }

  // ── Google Sign In With Google ──────────────────────────────────────────────
  const loginWithGoogle = async (credential: string) => {
    const res = await API.post('/auth/google', { credential })
    await _finalize(res.data.access_token)
  }

  // ── Facebook Login ──────────────────────────────────────────────────────────
  const loginWithFacebook = async (accessToken: string) => {
    const res = await API.post('/auth/facebook', { access_token: accessToken })
    await _finalize(res.data.access_token)
  }

  // ── Phone OTP ───────────────────────────────────────────────────────────────
  const sendPhoneOTP = async (phone: string) => {
    await API.post('/auth/phone/send-otp', { phone })
  }

  const loginWithPhone = async (phone: string, code: string) => {
    const res = await API.post('/auth/phone/verify-otp', { phone, code })
    await _finalize(res.data.access_token)
  }

  return (
    <AuthContext.Provider value={{
      user, token, loading,
      login, register,
      loginWithGoogle, loginWithFacebook, loginWithToken,
      sendPhoneOTP, loginWithPhone,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

