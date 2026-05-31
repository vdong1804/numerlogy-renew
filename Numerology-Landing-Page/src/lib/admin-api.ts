/**
 * Admin API fetch wrapper
 * Adds Bearer token, handles 401, provides typed helpers
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

const TOKEN_KEY = 'admin_access_token'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setAdminToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearAdminToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

function handleUnauthorized(): void {
  clearAdminToken()
  window.location.href = '/admin/login'
}

export async function adminFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const token = getToken()
  const headers: HeadersInit = {
    ...(init.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })

  if (res.status === 401) {
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

export async function uploadFile(file: File): Promise<{ url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const token = getToken()
  const res = await fetch(`${API_BASE}/admin/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })
  if (res.status === 401) {
    handleUnauthorized()
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg)
  }
  return res.json()
}
