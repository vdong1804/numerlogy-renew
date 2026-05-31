/**
 * Typed wrappers for /api/my/* endpoints.
 * All call sites require an authenticated session (userFetch handles 401).
 */

import { getJson, postJson, userFetch } from './user-api'

export interface MyDashboardSummary {
  quota_total: number
  quota_used: number
  quota_remaining: number
  active_package_id?: number | null
  active_package_name?: string | null
  active_package_total?: number | null
  active_package_acquired_at?: string | null
  active_package_expires_at?: string | null
  orders_count: number
  reports_count: number
  recent_orders?: MyOrderSummary[]
  recent_reports?: MyReport[]
}

export interface MyActivePackage {
  id: number
  package_id: number
  name: string
  quota_total: number
  quota_remaining: number
  acquired_at: string
  expires_at?: string | null
  is_active: boolean
}

export interface MyDownloadEntry {
  id: number
  name: string
  birth_day?: string | null
  gender?: string | null
  phone?: string | null
  type: number
  created_at: string
}

export interface MyProfile {
  id: number
  email: string
  first_name: string
  last_name: string
  name: string
  birth_day?: string | null
  address?: string | null
  phone?: string | null
  number_download: number
  notification_prefs: Record<string, unknown>
}

export interface MyProfileUpdate {
  name?: string
  birth_day?: string
  gender?: string
  phone?: string
  address?: string
}

export interface MyOrderItem {
  id: number
  product_id: number
  qty: number
  unit_price: number
  snapshot_name: string
}

export interface MyOrderSummary {
  id: number
  ref_code: string
  total_amount: number
  currency: string
  status: 'pending' | 'paid' | 'cancelled' | 'expired' | 'failed'
  paid_at?: string | null
  expires_at: string
  created_at: string
}

export interface MyOrderDetail extends MyOrderSummary {
  items: MyOrderItem[]
  meta: Record<string, unknown>
}

export interface MyReport {
  id: number
  order_id?: number | null
  product_id: number
  pdf_path: string
  generated_at: string
  input_payload: Record<string, unknown>
  download_count: number
  last_downloaded_at?: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface NotificationPrefs {
  order_paid_email: boolean
  quota_low_email: boolean
  marketing_email: boolean
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export const getDashboard = () => getJson<MyDashboardSummary>('/api/my/dashboard')

export const listOrders = (params: { limit?: number; offset?: number; status?: string } = {}) => {
  const qs = new URLSearchParams()
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  if (params.status) qs.set('status', params.status)
  return getJson<PaginatedResponse<MyOrderSummary>>(`/api/my/orders?${qs}`)
}

export const getOrderDetail = (id: number) =>
  getJson<MyOrderDetail>(`/api/my/orders/${id}`)

export const listReports = (params: { limit?: number; offset?: number } = {}) => {
  const qs = new URLSearchParams()
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  return getJson<PaginatedResponse<MyReport>>(`/api/my/reports?${qs}`)
}

/** Returns full URL the browser can open (auth header carried via fetch then `target=_blank` workaround). */
export async function downloadReportBlob(reportId: number): Promise<Blob> {
  const res = await userFetch(`/api/my/reports/${reportId}/download`)
  if (!res.ok) throw new Error(`Download failed: ${res.statusText}`)
  return res.blob()
}

export function reportPdfPublicUrl(report: MyReport): string {
  return `${API_BASE}/api/my/reports/${report.id}/download`
}

export const getNotifications = () =>
  getJson<NotificationPrefs>('/api/my/settings/notifications')

export async function updateNotifications(prefs: NotificationPrefs): Promise<NotificationPrefs> {
  const res = await userFetch('/api/my/settings/notifications', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(prefs),
  })
  if (!res.ok) throw new Error(`Update failed: ${res.statusText}`)
  return res.json() as Promise<NotificationPrefs>
}

export const changePassword = (old_password: string, new_password: string) =>
  postJson('/api/my/password', { old_password, new_password })

// ---------------------------------------------------------------------------
// Profile (/api/my/profile)
// ---------------------------------------------------------------------------

export const getMyProfile = () => getJson<MyProfile>('/api/my/profile')

export async function updateMyProfile(body: MyProfileUpdate): Promise<MyProfile> {
  const res = await userFetch('/api/my/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Update failed: ${res.statusText}`)
  return res.json() as Promise<MyProfile>
}

// ---------------------------------------------------------------------------
// Active packages (/api/my/packages)
// ---------------------------------------------------------------------------

export const listMyPackages = () => getJson<MyActivePackage[]>('/api/my/packages')

// ---------------------------------------------------------------------------
// Downloads history (/api/my/downloads)
// ---------------------------------------------------------------------------

export const listMyDownloads = (
  params: { limit?: number; offset?: number; type?: number } = {}
) => {
  const qs = new URLSearchParams()
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  if (params.type != null) qs.set('type', String(params.type))
  return getJson<PaginatedResponse<MyDownloadEntry>>(`/api/my/downloads?${qs}`)
}

// ---------------------------------------------------------------------------
// Invoice (/api/my/orders/{id}/invoice) — returns Blob
// ---------------------------------------------------------------------------

export async function downloadInvoiceBlob(orderId: number): Promise<Blob> {
  const res = await userFetch(`/api/my/orders/${orderId}/invoice`)
  if (!res.ok) throw new Error(`Invoice download failed: ${res.statusText}`)
  return res.blob()
}
