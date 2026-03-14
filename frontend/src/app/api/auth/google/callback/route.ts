import { NextRequest, NextResponse } from 'next/server'

/**
 * Google Sign In With Google — redirect-mode callback.
 * Google POSTs { credential } here after the user signs in.
 * We forward it to our FastAPI backend, get a JWT, and
 * redirect the browser to /auth/complete?token=<jwt>
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.formData()
    const credential = body.get('credential') as string | null

    if (!credential) {
      return NextResponse.redirect(new URL('/login?error=google_no_credential', req.url))
    }

    // Forward to FastAPI backend
    // Use 127.0.0.1 explicitly — on Windows, 'localhost' may resolve to ::1 (IPv6)
    // while the backend only listens on 127.0.0.1 (IPv4)
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    let res: Response
    try {
      res = await fetch(`${backendUrl}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      })
    } catch (fetchErr: any) {
      console.error('[Google callback] fetch to backend failed:', fetchErr.message)
      return NextResponse.redirect(new URL('/login?error=backend_unreachable', req.url))
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      console.error('[Google callback] backend error:', res.status, err)
      const msg = encodeURIComponent(err?.detail || 'google_auth_failed')
      return NextResponse.redirect(new URL(`/login?error=${msg}`, req.url))
    }

    const data = await res.json()
    const token = data.access_token as string

    // Redirect to /auth/complete — that page stores the token in localStorage
    const redirectUrl = new URL('/auth/complete', req.url)
    redirectUrl.searchParams.set('token', token)
    return NextResponse.redirect(redirectUrl)
  } catch (e: any) {
    console.error('[Google callback] error:', e)
    return NextResponse.redirect(new URL('/login?error=google_callback_error', req.url))
  }
}
