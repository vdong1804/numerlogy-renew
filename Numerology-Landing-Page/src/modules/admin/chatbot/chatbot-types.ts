/**
 * Shared types for the admin chatbot UI — mirror the FastAPI schemas in
 * `numerology-api/app/schemas/chat/admin.py` (snake_case wire format).
 */

export interface KbDocument {
  id: number
  source_type: string
  source_ref: string
  title: string | null
  metadata: Record<string, unknown>
  created_by: number | null
  created_at: string
  updated_at: string
  chunk_count: number
}

export interface KbDocumentListResponse {
  items: KbDocument[]
  total: number
  limit: number
  offset: number
}

export interface KbUploadResponse {
  document: KbDocument
  chunks_created: number
  file_kind: string
  char_count: number
}

export interface DailyMessageStat {
  day: string
  tier: string
  count: number
}

export interface CostByModel {
  model: string
  input_tokens: number
  output_tokens: number
  estimated_usd: number
}

export interface PromptOut {
  value: string
  is_override: boolean
  version: number | null
  updated_at: string | null
  updated_by: number | null
}

export interface PromptHistoryEntry {
  id: number
  value: string
  version: number
  changed_by: number | null
  changed_at: string
}

export interface PromptHistoryResponse {
  items: PromptHistoryEntry[]
}

export interface ConversationListItem {
  id: number
  user_id: number
  title: string | null
  pdf_context_id: number | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationListResponse {
  items: ConversationListItem[]
  total: number
  limit: number
  offset: number
}

export interface ConversationCitation {
  index?: number
  chunk_id?: number
  document_id?: number
  source_type?: string
  source_ref?: string
  title?: string | null
  score?: number
}

export interface ConversationMessage {
  id: number
  role: string
  content: string
  model_used: string | null
  tier: string | null
  input_tokens: number
  output_tokens: number
  citations: ConversationCitation[]
  created_at: string
}

export interface ConversationDetail {
  id: number
  user_id: number
  title: string | null
  pdf_context_id: number | null
  created_at: string
  updated_at: string
  messages: ConversationMessage[]
}

export interface AnalyticsOverview {
  window_start: string
  window_end: string
  total_messages: number
  total_conversations: number
  unique_users: number
  messages_by_day: DailyMessageStat[]
  top_questions: { question: string; count: number }[]
  cost_by_model: CostByModel[]
  estimated_total_cost_usd: number
  semantic_cache_entries: number
  semantic_cache_hits: number
  semantic_cache_hit_rate: number
  addon_purchases: number
}
