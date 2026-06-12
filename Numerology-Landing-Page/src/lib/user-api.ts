/**
 * User-site API fetch wrapper.
 * Adds Bearer token from cookies; 401 clears tokens and redirects to /login.
 */

import Cookies from 'js-cookie'

import { tryRefreshTokens } from './token-refresh'
import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE } from './user-auth'

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

function getToken(): string | undefined {
  return Cookies.get(ACCESS_TOKEN_COOKIE)
}

function handleUnauthorized(): void {
  Cookies.remove(ACCESS_TOKEN_COOKIE)
  Cookies.remove(REFRESH_TOKEN_COOKIE)
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

export async function userFetch(
  path: string,
  init: RequestInit = {},
  retried = false
): Promise<Response> {
  const token = getToken()
  const headers: HeadersInit = {
    ...(init.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (res.status === 401) {
    // Access token likely expired — try a one-time refresh, then replay once.
    if (!retried && !path.startsWith('/auth/refresh') && Cookies.get(REFRESH_TOKEN_COOKIE)) {
      const refreshed = await tryRefreshTokens()
      if (refreshed) return userFetch(path, init, true)
    }
    handleUnauthorized()
    throw new Error('Unauthorized')
  }
  return res
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((e: { msg?: string }) => e.msg ?? '')
        .filter(Boolean)
        .join('; ')
    }
    return res.statusText
  } catch {
    return res.statusText
  }
}

export async function getJson<T = unknown>(path: string): Promise<T> {
  const res = await userFetch(path)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function postJson<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await userFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  if (res.status === 204) return {} as T
  return res.json() as Promise<T>
}
