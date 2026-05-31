/**
 * User-site auth helpers — token cookies + /auth/me hook.
 * Token storage: js-cookie (access_token + refresh_token).
 */

import Cookies from 'js-cookie'
import { useRouter } from 'next/router'
import { useCallback, useEffect, useState } from 'react'

import { getJson, postJson } from './user-api'

export const ACCESS_TOKEN_COOKIE = 'access_token'
export const REFRESH_TOKEN_COOKIE = 'refresh_token'

export interface AuthUser {
  id: number
  email: string
  first_name: string
  last_name: string
  is_superuser: boolean
}

export interface TokenPair {
  access_token: string
  refresh_token: string
}

export function setUserTokens(tokens: TokenPair): void {
  const secure = process.env.NODE_ENV === 'production'
  // 7 days for refresh, access expiry handled by API
  Cookies.set(ACCESS_TOKEN_COOKIE, tokens.access_token, {
    sameSite: 'lax',
    secure,
  })
  Cookies.set(REFRESH_TOKEN_COOKIE, tokens.refresh_token, {
    sameSite: 'lax',
    secure,
    expires: 7,
  })
}

export function clearUserTokens(): void {
  Cookies.remove(ACCESS_TOKEN_COOKIE)
  Cookies.remove(REFRESH_TOKEN_COOKIE)
}

export function getAccessToken(): string | undefined {
  return Cookies.get(ACCESS_TOKEN_COOKIE)
}

export function getRefreshToken(): string | undefined {
  return Cookies.get(REFRESH_TOKEN_COOKIE)
}

interface UseUserAuthReturn {
  user: AuthUser | null
  loading: boolean
  refresh: () => Promise<void>
  logout: () => Promise<void>
}

export function useUserAuth(): UseUserAuthReturn {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await getJson<AuthUser>('/auth/me')
      setUser(me)
    } catch {
      clearUserTokens()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      try {
        await postJson('/auth/logout', { refresh_token: refreshToken })
      } catch {
        // ignore — clear locally regardless
      }
    }
    clearUserTokens()
    setUser(null)
    router.push('/')
  }, [router])

  return { user, loading, refresh: load, logout }
}
