/**
 * Single-flight access-token refresh shared by the user-site and admin HTTP clients.
 *
 * The backend ROTATES refresh tokens (one-time use — rotate_refresh revokes the
 * old token on every call). So when several requests get a 401 at the same time,
 * they MUST share one in-flight refresh call; otherwise the second call would
 * send an already-revoked refresh token and the user gets logged out anyway.
 * The closed-over `refreshPromise` guarantees that single-flight behaviour.
 *
 * The user site stores tokens in cookies; the admin console uses localStorage —
 * so the storage layer is injected via `getRefreshToken` / `storeTokens`.
 */

import Cookies from 'js-cookie'

import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE } from './user-auth'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

interface RefreshConfig {
  /** Read the currently stored raw refresh token, or null/undefined if none. */
  getRefreshToken: () => string | null | undefined
  /** Persist a freshly rotated access + refresh token pair. */
  storeTokens: (access: string, refresh: string) => void
}

/**
 * Build a `tryRefresh()` function bound to one storage backend. Concurrent
 * callers of the returned function share a single in-flight refresh request.
 */
export function createSingleFlightRefresh(
  config: RefreshConfig
): () => Promise<boolean> {
  let refreshPromise: Promise<boolean> | null = null

  async function doRefresh(refreshToken: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!res.ok) return false
      const data = (await res.json()) as {
        access_token?: string
        refresh_token?: string
      }
      if (!data.access_token || !data.refresh_token) return false
      config.storeTokens(data.access_token, data.refresh_token)
      return true
    } catch {
      return false
    }
  }

  return function tryRefresh(): Promise<boolean> {
    const refreshToken = config.getRefreshToken()
    if (!refreshToken) return Promise.resolve(false)
    if (!refreshPromise) {
      refreshPromise = doRefresh(refreshToken).finally(() => {
        refreshPromise = null
      })
    }
    return refreshPromise
  }
}

/** User-site refresher — tokens live in cookies (see user-auth.ts). */
export const tryRefreshTokens = createSingleFlightRefresh({
  getRefreshToken: () => Cookies.get(REFRESH_TOKEN_COOKIE),
  storeTokens: (access, refresh) => {
    const secure = process.env.NODE_ENV === 'production'
    Cookies.set(ACCESS_TOKEN_COOKIE, access, { sameSite: 'lax', secure })
    Cookies.set(REFRESH_TOKEN_COOKIE, refresh, {
      sameSite: 'lax',
      secure,
      expires: 7,
    })
  },
})
