/**
 * Chat domain types — conversations, messages, citations.
 * Source of truth: backend SSE contract in phase-04-streaming-ui.md
 */

export interface Conversation {
  id: number
  title: string
  createdAt: string
  pdfContextId?: number
}

export interface Citation {
  index: number
  chunkId: number
  documentId: number
  sourceType: string
  sourceRef: string
  title?: string
  score: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  createdAt: string
}

// ---------------------------------------------------------------------------
// Quota + Add-on types (Phase 05)
// ---------------------------------------------------------------------------

export interface Quota {
  freeUsedToday: number
  freeLimit: number
  addonRemaining: number
  addonTier: 'flash' | 'pro' | null
  addonExpiresAt: string | null
  canSend: boolean
  decisionSource: 'addon' | 'free' | null
}

export interface AddonPackage {
  id: number
  name: string
  price: number
  priceSale: number
  currency: string
  messageCount: number | null
  tier: 'flash' | 'pro' | null
  validityDays: number | null
  description: string | null
}

export interface AddonPurchaseInitiate {
  paymentId: number
  packageId: number
  price: number
  status: number
}

// ---------------------------------------------------------------------------
// SSE event payloads
// ---------------------------------------------------------------------------

/** Parsed SSE event payloads */
export interface SseDeltaEvent {
  token: string
}

export interface SseCitationsEvent {
  citations: Citation[]
}

export interface SseDoneEvent {
  message_id: number
  input_tokens: number
  output_tokens: number
  model_used: string
}

export interface SseErrorEvent {
  code: string
  message: string
}
