'use client'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'

// ─── Types injected by external scripts ──────────────────────────────────────
declare global {
  interface Window {
    google?: any
    FB?: any
    fbAsyncInit?: () => void
  }
}

interface Props {
  onError?: (msg: string) => void
}

export default function SocialAuthButtons({ onError }: Props) {
  const { loginWithFacebook, sendPhoneOTP, loginWithPhone } = useAuth()
  const router = useRouter()
  const googleBtnRef = useRef<HTMLDivElement>(null)

  // Phone OTP state
  const [phoneStep, setPhoneStep] = useState<'idle' | 'sending' | 'waiting' | 'verifying'>('idle')
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [phoneError, setPhoneError] = useState('')
  const [showPhoneModal, setShowPhoneModal] = useState(false)

  const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''
  const FB_APP_ID        = process.env.NEXT_PUBLIC_FACEBOOK_APP_ID  || ''

  // ── Google Sign In With Google ──────────────────────────────────────────────
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID.includes('your_google')) return

    const loadGoogle = () => {
      if (!window.google) return
      // Use redirect mode — avoids popup-blocker issues entirely.
      // Google POSTs the credential to /api/auth/google/callback,
      // which forwards it to FastAPI and then redirects to /auth/complete.
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        ux_mode: 'redirect',
        login_uri: `${window.location.origin}/api/auth/google/callback`,
      })
      if (googleBtnRef.current) {
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: 'filled_black',
          size: 'large',
          width: '100%',
          text: 'continue_with',
          shape: 'rectangular',
        })
      }
    }

    if (window.google) {
      loadGoogle()
    } else {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true
      script.onload = loadGoogle
      document.head.appendChild(script)
    }
  }, [GOOGLE_CLIENT_ID])

  // ── Facebook Login ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!FB_APP_ID || FB_APP_ID.includes('your_facebook')) return

    window.fbAsyncInit = () => {
      window.FB.init({ appId: FB_APP_ID, cookie: true, xfbml: true, version: 'v20.0' })
    }

    if (!document.getElementById('fb-jssdk')) {
      const script = document.createElement('script')
      script.id = 'fb-jssdk'
      script.src = 'https://connect.facebook.net/en_US/sdk.js'
      script.async = true
      script.defer = true
      document.head.appendChild(script)
    }
  }, [FB_APP_ID])

  const handleFacebook = () => {
    if (!window.FB) { onError?.('Facebook SDK not loaded yet. Try again.'); return }
    window.FB.login(async (response: any) => {
      if (response.authResponse?.accessToken) {
        try {
          await loginWithFacebook(response.authResponse.accessToken)
          router.push('/dashboard/buyer')
        } catch (e: any) {
          onError?.(e?.response?.data?.detail || 'Facebook sign-in failed')
        }
      } else {
        onError?.('Facebook login cancelled')
      }
    }, { scope: 'public_profile,email' })
  }

  // ── Phone OTP ───────────────────────────────────────────────────────────────
  const handleSendOTP = async () => {
    setPhoneError('')
    if (!phone.trim() || phone.replace(/\D/g, '').length < 7) {
      setPhoneError('Enter a valid phone number in E.164 format, e.g. +923001234567')
      return
    }
    setPhoneStep('sending')
    try {
      await sendPhoneOTP(phone.trim())
      setPhoneStep('waiting')
    } catch (e: any) {
      const status = e?.response?.status
      const detail = e?.response?.data?.detail || 'Failed to send OTP'
      if (status === 503) {
        setPhoneError('Phone auth not configured on server. Add Twilio credentials to .env.')
      } else {
        setPhoneError(detail)
      }
      setPhoneStep('idle')
    }
  }

  const handleVerifyOTP = async () => {
    setPhoneError('')
    setPhoneStep('verifying')
    try {
      await loginWithPhone(phone.trim(), otp.trim())
      setShowPhoneModal(false)
      router.push('/dashboard/buyer')
    } catch (e: any) {
      const status = e?.response?.status
      const detail = e?.response?.data?.detail || 'Invalid OTP'
      if (status === 503) {
        setPhoneError('Phone auth not configured on server. Add Twilio credentials to .env.')
      } else {
        setPhoneError(detail)
      }
      setPhoneStep('waiting')
    }
  }

  const configured = {
    google:   GOOGLE_CLIENT_ID && !GOOGLE_CLIENT_ID.includes('your_google'),
    facebook: FB_APP_ID        && !FB_APP_ID.includes('your_facebook'),
  }

  return (
    <div className="space-y-3 mt-4">
      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-[#2a2a45]" />
        <span className="text-zinc-500 text-xs">or continue with</span>
        <div className="flex-1 h-px bg-[#2a2a45]" />
      </div>

      {/* Google */}
      {configured.google ? (
        <div ref={googleBtnRef} className="w-full rounded-xl overflow-hidden" />
      ) : (
        <button
          disabled
          className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl bg-[#1e1e35] border border-[#2a2a45] text-zinc-500 text-sm cursor-not-allowed"
          title="Set NEXT_PUBLIC_GOOGLE_CLIENT_ID in .env.local"
        >
          <GoogleIcon /> Google <span className="text-xs text-zinc-600">(not configured)</span>
        </button>
      )}

      {/* Facebook */}
      <button
        onClick={configured.facebook ? handleFacebook : undefined}
        disabled={!configured.facebook}
        className={`w-full flex items-center justify-center gap-3 py-2.5 rounded-xl border text-sm font-medium transition-all
          ${configured.facebook
            ? 'bg-[#1877F2] border-[#1877F2] text-white hover:bg-[#166fe5] cursor-pointer'
            : 'bg-[#1e1e35] border-[#2a2a45] text-zinc-500 cursor-not-allowed'}`}
        title={!configured.facebook ? 'Set NEXT_PUBLIC_FACEBOOK_APP_ID in .env.local' : ''}
      >
        <FacebookIcon />
        Continue with Facebook
        {!configured.facebook && <span className="text-xs text-zinc-600 ml-1">(not configured)</span>}
      </button>

      {/* Phone */}
      <button
        onClick={() => { setShowPhoneModal(true); setPhoneStep('idle'); setPhone(''); setOtp(''); setPhoneError('') }}
        className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl bg-[#1a1a2e] border border-[#3a3a5c] text-white text-sm font-medium hover:border-violet-500 hover:bg-[#22223a] transition-all cursor-pointer"
      >
        <PhoneIcon /> Continue with Phone (OTP)
      </button>

      {/* Phone OTP Modal */}
      {showPhoneModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm bg-[#1a1a2e] border border-[#2a2a45] rounded-2xl p-7 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-1">Phone Verification</h3>
            <p className="text-zinc-400 text-sm mb-5">
              {phoneStep === 'waiting' || phoneStep === 'verifying'
                ? `Enter the 6-digit code sent to ${phone}`
                : 'Enter your mobile number to receive a one-time code'}
            </p>

            {phoneError && (
              <div className="bg-red-900/40 text-red-400 text-sm px-4 py-2 rounded-lg mb-4">{phoneError}</div>
            )}

            {(phoneStep === 'idle' || phoneStep === 'sending') && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-zinc-400 block mb-1">Phone Number (E.164: +923001234567)</label>
                  <input
                    type="tel"
                    placeholder="+1 (555) 000-0000"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500"
                  />
                </div>
                <button
                  onClick={handleSendOTP}
                  disabled={phoneStep === 'sending' || phone.length < 7}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold disabled:opacity-50"
                >
                  {phoneStep === 'sending' ? 'Sending OTP...' : 'Send OTP'}
                </button>
              </div>
            )}

            {(phoneStep === 'waiting' || phoneStep === 'verifying') && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-zinc-400 block mb-1">6-Digit OTP Code</label>
                  <input
                    type="text"
                    placeholder="123456"
                    maxLength={6}
                    value={otp}
                    onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
                    className="w-full bg-[#0f0f1a] border border-[#3a3a5c] rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500 tracking-[0.4em] text-center text-xl"
                  />
                </div>
                <button
                  onClick={handleVerifyOTP}
                  disabled={phoneStep === 'verifying' || otp.length !== 6}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold disabled:opacity-50"
                >
                  {phoneStep === 'verifying' ? 'Verifying...' : 'Verify & Sign In'}
                </button>
                <button
                  onClick={() => setPhoneStep('idle')}
                  className="w-full text-zinc-500 text-sm hover:text-zinc-300 transition-colors"
                >
                  ← Change number
                </button>
              </div>
            )}

            <button
              onClick={() => setShowPhoneModal(false)}
              className="mt-4 w-full text-zinc-600 text-xs hover:text-zinc-400 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── SVG Icons ────────────────────────────────────────────────────────────────
function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

function FacebookIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="white">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  )
}

function PhoneIcon() {
  return (
    <svg className="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
    </svg>
  )
}
