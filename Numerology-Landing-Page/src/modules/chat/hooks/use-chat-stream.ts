/**
 * useChatStream — SSE consumer for POST /api/chat/conversations/{id}/messages/stream
 *
 * SSE contract (phase-04-streaming-ui.md):
 *   event: delta       data: {"token":"<str>"}
 *   event: citations   data: {"citations":[...]}
 *   event: done        data: {"message_id":123,...}
 *   event: error       data: {"code":"...","message":"..."}
 *
 * Token batching: tokens accumulate in a ref and flush to state every rAF frame
 * (~16ms) to avoid per-token re-render storm.
 * fullTextRef tracks cumulative text to avoid stale-closure issues on `done`.
 */

import Cookies from 'js-cookie'
import { useCallback, useEffect, useRef, useState } from 'react'

import { ACCESS_TOKEN_COOKIE } from '@/lib/user-auth'
import type {
  Citation,
  Message,
  SseDoneEvent,
  SseErrorEvent,
} from '@/models/Chat'

import type { CitationRaw } from '../api/chat-api'
import { toCitation } from '../api/chat-api'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

interface UseChatStreamOptions {
  /** Called when backend signals quota_exceeded (SSE error or 402 HTTP). */
  onQuotaExceeded?: () => void
  /** Called when backend returns 429 rate-limit response (SSE or HTTP). */
  onRateLimited?: (
    retryAfter: number,
    reason: 'bucket_empty' | 'daily_cap'
  ) => void
}

interface UseChatStreamReturn {
  send: (content: string, pdfContextId?: number) => Promise<void>
  streamingText: string
  streamingCitations: Citation[]
  isStreaming: boolean
  error: string | null
  cancel: () => void
}

export function useChatStream(
  convId: number | null,
  onMessageComplete: (msg: Message) => void,
  options: UseChatStreamOptions = {}
): UseChatStreamReturn {
  const { onQuotaExceeded, onRateLimited } = options
  // Store callbacks in refs so `send` always calls latest version without
  // needing to re-create the memoised callback on every render (H2).
  const onQuotaExceededRef = useRef(onQuotaExceeded)
  useEffect(() => {
    onQuotaExceededRef.current = onQuotaExceeded
  }, [onQuotaExceeded])
  const onRateLimitedRef = useRef(onRateLimited)
  useEffect(() => {
    onRateLimitedRef.current = onRateLimited
  }, [onRateLimited])

  const [streamingText, setStreamingText] = useState('')
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Pending tokens not yet flushed to state
  const pendingRef = useRef('')
  // Full accumulated text (avoids stale-closure on `done`)
  const fullTextRef = useRef('')
  const rafRef = useRef<number | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const flushTokens = useCallback(() => {
    if (pendingRef.current) {
      fullTextRef.current += pendingRef.current
      setStreamingText((prev) => prev + pendingRef.current)
      pendingRef.current = ''
    }
    rafRef.current = null
  }, [])

  const scheduleFlush = useCallback(() => {
    if (rafRef.current == null) {
      rafRef.current = requestAnimationFrame(flushTokens)
    }
  }, [flushTokens])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    pendingRef.current = ''
    fullTextRef.current = ''
    setIsStreaming(false)
  }, [])

  const send = useCallback(
    async (content: string, pdfContextId?: number) => {
      if (convId == null) return
      const token = Cookies.get(ACCESS_TOKEN_COOKIE)
      if (!token) {
        window.location.href = '/login'
        return
      }

      // Reset state
      setStreamingText('')
      setStreamingCitations([])
      setError(null)
      setIsStreaming(true)
      pendingRef.current = ''
      fullTextRef.current = ''

      const ctrl = new AbortController()
      abortRef.current = ctrl

      try {
        const res = await fetch(
          `${API_BASE}/api/chat/conversations/${convId}/messages/stream`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
              Accept: 'text/event-stream',
            },
            body: JSON.stringify({
              content,
              ...(pdfContextId != null ? { pdf_context_id: pdfContextId } : {}),
            }),
            signal: ctrl.signal,
          }
        )

        if (!res.ok) {
          if (res.status === 402) {
            try {
              const body = (await res.json()) as { detail?: { code?: string } }
              if (body?.detail?.code === 'quota_exceeded') {
                onQuotaExceededRef.current?.()
                setIsStreaming(false)
                return
              }
            } catch {
              // fall through to generic error
            }
          }
          if (res.status === 429) {
            try {
              const body = (await res.json()) as {
                detail?: {
                  code?: string
                  retry_after?: number
                  reason?: string
                }
              }
              const detail = body?.detail
              const retryAfter =
                typeof detail?.retry_after === 'number'
                  ? detail.retry_after
                  : parseInt(res.headers.get('Retry-After') ?? '0', 10)
              const reason = (
                detail?.reason === 'daily_cap' ? 'daily_cap' : 'bucket_empty'
              ) as 'bucket_empty' | 'daily_cap'
              onRateLimitedRef.current?.(retryAfter, reason)
              setIsStreaming(false)
              return
            } catch {
              // fall through to generic error
            }
          }
          throw new Error(`Lỗi máy chủ: ${res.status} ${res.statusText}`)
        }
        if (!res.body) throw new Error('Không nhận được luồng dữ liệu')

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let finalCitations: Citation[] = []
        let completedMessage: Message | null = null

        /** Parse one SSE frame string into { eventType, dataLine } */
        const parseFrame = (
          frame: string
        ): { eventType: string; dataLine: string } => {
          let eventType = 'message'
          let dataLine = ''
          frame.split('\n').forEach((line) => {
            if (line.startsWith('event:')) eventType = line.slice(6).trim()
            else if (line.startsWith('data:')) dataLine = line.slice(5).trim()
          })
          return { eventType, dataLine }
        }

        /** Process a single parsed SSE frame — mutates outer let vars */
        const handleFrame = (eventType: string, dataLine: string): void => {
          if (!dataLine) return
          try {
            const parsed: unknown = JSON.parse(dataLine)
            if (eventType === 'delta') {
              const { token: tok } = parsed as { token: string }
              pendingRef.current += tok
              scheduleFlush()
            } else if (eventType === 'citations') {
              const { citations } = parsed as { citations: CitationRaw[] }
              // Map snake_case wire shape to camelCase Citation so streaming and
              // rehydrated messages have identical shape (fixes C2).
              const mapped = citations.map(toCitation)
              finalCitations = mapped
              setStreamingCitations(mapped)
            } else if (eventType === 'done') {
              const meta = parsed as SseDoneEvent
              if (rafRef.current != null) {
                cancelAnimationFrame(rafRef.current)
                rafRef.current = null
              }
              fullTextRef.current += pendingRef.current
              pendingRef.current = ''
              completedMessage = {
                id: meta.message_id,
                role: 'assistant',
                content: fullTextRef.current,
                citations: finalCitations,
                createdAt: new Date().toISOString(),
              }
            } else if (eventType === 'error') {
              const errPayload = parsed as SseErrorEvent
              if (
                errPayload.code === 'quota_exceeded' ||
                errPayload.code === 'quota_exceeded_postcommit'
              ) {
                onQuotaExceededRef.current?.()
                // Terminate stream cleanly — not an unexpected error
                setIsStreaming(false)
                return
              }
              throw new Error(errPayload.message)
            }
          } catch (parseErr) {
            if (eventType === 'error') throw parseErr
            // Ignore malformed keep-alive frames
          }
        }

        // Iterative stream read — replaces recursive pump() to avoid stack overflow
        // on very long responses. The lint-disables are intentional for streaming I/O.
        // eslint-disable-next-line no-constant-condition
        while (true) {
          // eslint-disable-next-line no-await-in-loop
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const frames = buffer.split('\n\n')
          buffer = frames.pop() ?? ''
          frames
            .filter((f) => f.trim().length > 0)
            .map(parseFrame)
            .forEach(({ eventType, dataLine }) =>
              handleFrame(eventType, dataLine)
            )
        }

        // Final flush of any remaining pending tokens
        if (rafRef.current != null) {
          cancelAnimationFrame(rafRef.current)
          rafRef.current = null
        }
        if (pendingRef.current) {
          fullTextRef.current += pendingRef.current
          pendingRef.current = ''
        }

        if (completedMessage) {
          onMessageComplete(completedMessage)
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        const msg = (err as Error).message || 'Đã xảy ra lỗi khi nhận phản hồi'
        setError(msg)
      } finally {
        setIsStreaming(false)
        setStreamingText('')
        setStreamingCitations([])
        pendingRef.current = ''
        fullTextRef.current = ''
      }
    },
    [convId, scheduleFlush, onMessageComplete]
  )

  return { send, streamingText, streamingCitations, isStreaming, error, cancel }
}
