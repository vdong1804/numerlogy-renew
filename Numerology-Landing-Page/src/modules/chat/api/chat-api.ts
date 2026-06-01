/**
 * Chat API wrappers — conversations, messages, PDF upload.
 * Reuses userFetch/getJson/postJson from lib/user-api (JWT Bearer injected there).
 * Do NOT add auth logic here.
 *
 * All REST responses are wrapped by backend: { data: T, ... }.
 * getData/postData helpers unwrap locally; shared getJson is untouched.
 */

import { getJson, userFetch } from '@/lib/user-api'
import type {
  AddonPackage,
  AddonPurchaseInitiate,
  Citation,
  Conversation,
  Message,
  Quota,
} from '@/models/Chat'

// ---------------------------------------------------------------------------
// Local envelope helpers (do NOT touch getJson in lib/user-api)
// ---------------------------------------------------------------------------

async function getData<T>(path: string): Promise<T> {
  const env = await getJson<{ data: T }>(path)
  return env.data
}

// ---------------------------------------------------------------------------
// Quota + Add-on (Phase 05)
// ---------------------------------------------------------------------------

interface QuotaRaw {
  free_used_today: number
  free_limit: number
  addon_remaining: number
  addon_tier: string | null
  addon_expires_at: string | null
  can_send: boolean
  decision_source: 'addon' | 'free' | null
}

function toQuota(r: QuotaRaw): Quota {
  return {
    freeUsedToday: r.free_used_today,
    freeLimit: r.free_limit,
    addonRemaining: r.addon_remaining,
    addonTier: (r.addon_tier as Quota['addonTier']) ?? null,
    addonExpiresAt: r.addon_expires_at,
    canSend: r.can_send,
    decisionSource: r.decision_source,
  }
}

interface AddonPackageRaw {
  id: number
  name: string
  price: number
  price_sale: number
  currency: string
  message_count: number | null
  tier: string | null
  validity_days: number | null
  description: string | null
}

function toAddonPackage(r: AddonPackageRaw): AddonPackage {
  return {
    id: r.id,
    name: r.name,
    price: r.price,
    priceSale: r.price_sale,
    currency: r.currency,
    messageCount: r.message_count,
    tier: (r.tier as AddonPackage['tier']) ?? null,
    validityDays: r.validity_days,
    description: r.description,
  }
}

interface AddonPurchaseInitiateRaw {
  payment_id: number
  package_id: number
  price: number
  status: number
}

function toAddonPurchaseInitiate(
  r: AddonPurchaseInitiateRaw
): AddonPurchaseInitiate {
  return {
    paymentId: r.payment_id,
    packageId: r.package_id,
    price: r.price,
    status: r.status,
  }
}

export async function getQuota(): Promise<Quota> {
  const raw = await getData<QuotaRaw>('/api/chat/quota')
  return toQuota(raw)
}

export async function listAddons(): Promise<AddonPackage[]> {
  const raw = await getData<AddonPackageRaw[]>('/api/chat/addons')
  return raw.map(toAddonPackage)
}

export async function purchaseAddon(
  packageId: number
): Promise<AddonPurchaseInitiate> {
  const res = await userFetch(`/api/chat/addons/${packageId}/purchase`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) throw new Error(`Mua gói thất bại: ${res.statusText}`)
  const env: { data: AddonPurchaseInitiateRaw } = await res.json()
  return toAddonPurchaseInitiate(env.data)
}

// ---------------------------------------------------------------------------
// Addon payment snapshot (for the dedicated /chat/payment/[id] page)
// ---------------------------------------------------------------------------

interface AddonPaymentRaw {
  payment_id: number
  package_id: number
  package_name: string | null
  price: number
  status: number
}

export interface AddonPayment {
  paymentId: number
  packageId: number
  packageName: string | null
  price: number
  /** 1=pending, 2=approved, 3=rejected */
  status: number
}

function toAddonPayment(r: AddonPaymentRaw): AddonPayment {
  return {
    paymentId: r.payment_id,
    packageId: r.package_id,
    packageName: r.package_name,
    price: r.price,
    status: r.status,
  }
}

export async function getAddonPayment(
  paymentId: number
): Promise<AddonPayment> {
  const raw = await getData<AddonPaymentRaw>(
    `/api/chat/addons/payments/${paymentId}`
  )
  return toAddonPayment(raw)
}

// ---------------------------------------------------------------------------
// Conversations
// ---------------------------------------------------------------------------

export interface ConversationCreatePayload {
  title?: string
}

export interface ConversationRaw {
  id: number
  title: string
  created_at: string
  pdf_context_id?: number
}

function toConversation(r: ConversationRaw): Conversation {
  return {
    id: r.id,
    title: r.title,
    createdAt: r.created_at,
    pdfContextId: r.pdf_context_id,
  }
}

export async function listConversations(): Promise<Conversation[]> {
  // Backend: { data: ConversationRaw[], total, limit, offset }
  const raw = await getData<ConversationRaw[]>('/api/chat/conversations')
  return raw.map(toConversation)
}

export async function createConversation(
  title?: string
): Promise<Conversation> {
  const res = await userFetch('/api/chat/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title ?? 'Cuộc trò chuyện mới' }),
  })
  if (!res.ok)
    throw new Error(`Tạo cuộc trò chuyện thất bại: ${res.statusText}`)
  // Backend: { data: ConversationRaw }
  const env: { data: ConversationRaw } = await res.json()
  return toConversation(env.data)
}

export async function deleteConversation(id: number): Promise<void> {
  const res = await userFetch(`/api/chat/conversations/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`Xóa thất bại: ${res.statusText}`)
  // 204 no body — nothing to unwrap
}

// ---------------------------------------------------------------------------
// Messages
// ---------------------------------------------------------------------------

/** Wire shape from backend (snake_case) — used on both REST and SSE paths */
export interface CitationRaw {
  index: number
  chunk_id: number
  document_id: number
  source_type: string
  source_ref: string
  title?: string
  score: number
}

/** Maps backend snake_case citation to camelCase Citation */
export function toCitation(r: CitationRaw): Citation {
  return {
    index: r.index,
    chunkId: r.chunk_id,
    documentId: r.document_id,
    sourceType: r.source_type,
    sourceRef: r.source_ref,
    title: r.title,
    score: r.score,
  }
}

export interface MessageRaw {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations?: CitationRaw[]
  created_at: string
}

function toMessage(r: MessageRaw): Message {
  return {
    id: r.id,
    role: r.role,
    content: r.content,
    citations: (r.citations ?? []).map(toCitation),
    createdAt: r.created_at,
  }
}

export async function listMessages(convId: number): Promise<Message[]> {
  // Backend: { data: MessageRaw[] }
  const raw = await getData<MessageRaw[]>(
    `/api/chat/conversations/${convId}/messages`
  )
  return raw.map(toMessage)
}

// ---------------------------------------------------------------------------
// PDF context management
// ---------------------------------------------------------------------------

/**
 * Clears server-side pdf_context_id for a conversation.
 * PATCH /api/chat/conversations/{id}/pdf-context  body: { pdf_context_id: null }
 */
export async function clearPdfContext(conversationId: number): Promise<void> {
  const res = await userFetch(
    `/api/chat/conversations/${conversationId}/pdf-context`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pdf_context_id: null }),
    }
  )
  if (!res.ok) throw new Error(`Xóa PDF thất bại: ${res.statusText}`)
}

// ---------------------------------------------------------------------------
// PDF upload
// ---------------------------------------------------------------------------

/** Wire format returned by POST /api/chat/conversations/{id}/upload-pdf */
interface PdfUploadRaw {
  pdf_context_id: number
  matched: boolean
  matched_report_id: number | null
  page_count: number
  chunks_created: number
  expires_at: string
}

/** Camel-cased shape exposed to the rest of the frontend */
export interface PdfUploadResult {
  pdfContextId: number
  matched: boolean
  matchedReportId: number | null
  pageCount: number
  chunksCreated: number
  expiresAt: string
}

function toPdfUploadResult(r: PdfUploadRaw): PdfUploadResult {
  return {
    pdfContextId: r.pdf_context_id,
    matched: r.matched,
    matchedReportId: r.matched_report_id,
    pageCount: r.page_count,
    chunksCreated: r.chunks_created,
    expiresAt: r.expires_at,
  }
}

/**
 * Upload a PDF into an existing conversation.
 * Backend path: POST /api/chat/conversations/{conversationId}/upload-pdf
 * Requires conversationId — conversation must exist and be owned by user.
 */
export async function uploadPdf(
  conversationId: number,
  file: File
): Promise<PdfUploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await userFetch(
    `/api/chat/conversations/${conversationId}/upload-pdf`,
    { method: 'POST', body: form }
  )
  if (!res.ok) throw new Error(`Tải PDF thất bại: ${res.statusText}`)
  // Backend: { data: PdfUploadRaw }
  const env: { data: PdfUploadRaw } = await res.json()
  return toPdfUploadResult(env.data)
}
