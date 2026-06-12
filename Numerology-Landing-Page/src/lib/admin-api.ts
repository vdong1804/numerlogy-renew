/**
 * Admin API fetch wrapper
 * Adds Bearer token, handles 401 (with refresh-and-retry), provides typed helpers
 */

import { createSingleFlightRefresh } from './token-refresh'

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

const TOKEN_KEY = 'admin_access_token'
const REFRESH_TOKEN_KEY = 'admin_refresh_token'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setAdminToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/** Store the access + refresh pair returned by /auth/login. */
export function setAdminTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearAdminToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// Admin refresher — tokens live in localStorage (single-flight, shared rotation).
const tryRefreshAdminTokens = createSingleFlightRefresh({
  getRefreshToken,
  storeTokens: setAdminTokens,
})

function handleUnauthorized(): void {
  clearAdminToken()
  window.location.href = '/admin/login'
}

export async function adminFetch(
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
    if (!retried && !path.startsWith('/auth/refresh') && getRefreshToken()) {
      const refreshed = await tryRefreshAdminTokens()
      if (refreshed) return adminFetch(path, init, true)
    }
    handleUnauthorized()
    throw new Error('Unauthorized')
  }

  return res
}

export async function getJson<T = unknown>(path: string): Promise<T> {
  const res = await adminFetch(path)
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export async function postJson<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await adminFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export async function putJson<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await adminFetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export async function patchJson<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await adminFetch(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export async function del<T = unknown>(path: string): Promise<T> {
  const res = await adminFetch(path, { method: 'DELETE' })
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  // 204 No Content
  if (res.status === 204) return {} as T
  return res.json() as Promise<T>
}

export async function uploadFile(
  file: File,
  retried = false
): Promise<{ url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const token = getToken()
  const res = await fetch(`${API_BASE}/admin/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })
  if (res.status === 401) {
    // Access token likely expired — try a one-time refresh, then replay once.
    if (!retried && getRefreshToken()) {
      const refreshed = await tryRefreshAdminTokens()
      if (refreshed) return uploadFile(file, true)
    }
    handleUnauthorized()
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json()
}
