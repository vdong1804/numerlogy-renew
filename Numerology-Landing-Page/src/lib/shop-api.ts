/**
 * Shop & orders client — typed wrappers around userFetch.
 *
 * Public endpoints (catalogue) work without auth.
 * /api/orders endpoints require a Bearer token via userFetch.
 */

import { getJson, postJson, userFetch } from './user-api'

export type ProductType = 'package' | 'report' | 'combo'

export interface Product {
  id: number
  sku: string
  type: ProductType
  name: string
  slug: string
  description?: string | null
  price: number
  currency: string
  quota?: number | null
  renewal_days?: number | null
  template_name?: string | null
  content_codes?: string[] | null
  is_active: boolean
  sort_order: number
  meta: Record<string, unknown>
}

export type OrderStatus = 'pending' | 'paid' | 'cancelled' | 'expired' | 'failed'

export interface OrderItem {
  id: number
  product_id: number
  qty: number
  unit_price: number
  snapshot_name: string
}

export interface Order {
  id: number
  user_id: number
  ref_code: string
  total_amount: number
  currency: string
  status: OrderStatus
  payment_method: string
  expires_at: string
  paid_at?: string | null
  items: OrderItem[]
  meta: Record<string, unknown>
  created_at: string
}

export interface OrderStatusInfo {
  id: number
  ref_code: string
  status: OrderStatus
  paid_at?: string | null
}

export interface OrderCreateRequest {
  items: Array<{ product_id: number; qty?: number }>
  input_payload?: Record<string, unknown>
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

/** Public catalogue — does NOT use userFetch (no auth required). */
export async function listProducts(type?: ProductType): Promise<Product[]> {
  const url = new URL(`${API_BASE}/api/shop/products`)
  if (type) url.searchParams.set('type', type)
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(`Failed to load products: ${res.statusText}`)
  const data: { data: Product[] } = await res.json()
  return data.data
}

/** Public product detail by slug — no auth required. */
export async function getProductBySlug(slug: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/api/shop/products/${slug}`)
  if (res.status === 404) throw new Error('not_found')
  if (!res.ok) throw new Error(`Failed to load product: ${res.statusText}`)
  return res.json() as Promise<Product>
}

/** Auth required — creates a pending order, returns ref_code etc. */
export async function createOrder(body: OrderCreateRequest): Promise<Order> {
  return postJson<Order>('/api/orders', body)
}

export async function getOrder(orderId: number): Promise<Order> {
  return getJson<Order>(`/api/orders/${orderId}`)
}

export async function getOrderStatus(orderId: number): Promise<OrderStatusInfo> {
  // Use userFetch directly to avoid noisy /login redirect on transient errors
  const res = await userFetch(`/api/orders/${orderId}/status`)
  if (!res.ok) throw new Error(`Failed to poll order: ${res.statusText}`)
  return res.json() as Promise<OrderStatusInfo>
}
