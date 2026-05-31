/**
 * Typed wrappers for the new /admin/dashboard/*, /admin/orders, /admin/webhook-events endpoints.
 */

import { getJson, postJson } from './admin-api'

export interface DashboardKpi {
  revenue_today: number
  revenue_week: number
  revenue_month: number
  pending_orders: number
  paid_orders: number
}

export interface RevenuePoint {
  date: string
  revenue: number
}

export interface TopProduct {
  product_id: number
  name: string
  sku: string
  revenue: number
  qty: number
}

export interface AdminOrderSummary {
  id: number
  user_id: number
  ref_code: string
  total_amount: number
  currency: string
  status: 'pending' | 'paid' | 'cancelled' | 'expired' | 'failed'
  payment_method: string
  expires_at: string
  paid_at?: string | null
  items: Array<{
    id: number
    product_id: number
    qty: number
    unit_price: number
    snapshot_name: string
  }>
  meta: Record<string, unknown>
  created_at: string
}

export interface AdminWebhookEvent {
  id: number
  provider: string
  sepay_tx_id: string
  status: string
  order_id?: number | null
  ref_code?: string | null
  amount?: number | null
  error_message?: string | null
  created_at?: string | null
  raw_payload: Record<string, unknown>
}

export interface Paginated<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export const getDashboardMetrics = () => getJson<DashboardKpi>('/admin/dashboard/metrics')
export const getRevenueChart = () =>
  getJson<{ data: RevenuePoint[] }>('/admin/dashboard/revenue-chart')
export const getTopProducts = () =>
  getJson<{ data: TopProduct[] }>('/admin/dashboard/top-products')
export const refreshDashboard = () => postJson('/admin/dashboard/refresh', {})

export const listAdminOrders = (params: { limit?: number; offset?: number; status?: string } = {}) => {
  const qs = new URLSearchParams()
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  if (params.status) qs.set('status', params.status)
  return getJson<Paginated<AdminOrderSummary>>(`/admin/orders?${qs}`)
}

export interface OrderSearchFilters {
  email?: string
  ref_code?: string
  status?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

/** GET /admin/orders with advanced search params */
export const searchOrders = (filters: OrderSearchFilters = {}) => {
  const qs = new URLSearchParams()
  if (filters.email) qs.set('email', filters.email)
  if (filters.ref_code) qs.set('ref_code', filters.ref_code)
  if (filters.status) qs.set('status', filters.status)
  if (filters.date_from) qs.set('date_from', filters.date_from)
  if (filters.date_to) qs.set('date_to', filters.date_to)
  const page = filters.page ?? 0
  const size = filters.page_size ?? 50
  qs.set('limit', String(size))
  qs.set('offset', String(page * size))
  return getJson<Paginated<AdminOrderSummary>>(`/admin/orders?${qs}`)
}

/**
 * GET /admin/orders/export.csv — returns Blob and triggers browser download.
 * Filename: orders-YYYYMMDD.csv
 */
export async function exportOrdersCsv(filters: OrderSearchFilters = {}): Promise<void> {
  const qs = new URLSearchParams()
  if (filters.email) qs.set('email', filters.email)
  if (filters.ref_code) qs.set('ref_code', filters.ref_code)
  if (filters.status) qs.set('status', filters.status)
  if (filters.date_from) qs.set('date_from', filters.date_from)
  if (filters.date_to) qs.set('date_to', filters.date_to)

  const { adminFetch } = await import('./admin-api')
  const res = await adminFetch(`/admin/orders/export.csv?${qs}`)
  if (!res.ok) {
    // Parse FastAPI JSON error body ({"detail": "..."}) for a human-readable message.
    // Fall back to status text if body is not JSON.
    const errMsg = await res.json()
      .then((j: { detail?: string }) => j.detail ?? res.statusText)
      .catch(() => res.statusText)
    throw new Error(errMsg)
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const a = document.createElement('a')
  a.href = url
  a.download = `orders-${date}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const getAdminOrder = (id: number) =>
  getJson<AdminOrderSummary>(`/admin/orders/${id}`)

export const markOrderPaid = (id: number) =>
  postJson<{ status: string; order_id: number; ref_code?: string }>(`/admin/orders/${id}/mark-paid`, {})

/** POST /admin/orders/{id}/refund — backend endpoint created by Phase 02 agent */
export const refundOrder = (id: number, reason: string) =>
  postJson<{ status: string; order_id: number }>(`/admin/orders/${id}/refund`, { reason })

export const listAdminWebhookEvents = (params: { limit?: number; offset?: number; status?: string } = {}) => {
  const qs = new URLSearchParams()
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  if (params.status) qs.set('status', params.status)
  return getJson<Paginated<AdminWebhookEvent>>(`/admin/webhook-events?${qs}`)
}
