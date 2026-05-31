/**
 * useMessages — fetch message history for a conversation.
 * Initial page only — TODO: add infinite scroll (react-query + cursor pagination).
 */

import { useCallback, useEffect, useState } from 'react'

import type { Message } from '@/models/Chat'

import { listMessages } from '../api/chat-api'

interface UseMessagesReturn {
  messages: Message[]
  loading: boolean
  error: string | null
  append: (msg: Message) => void
  refresh: () => Promise<void>
}

export function useMessages(convId: number | null): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (convId == null) return
    setLoading(true)
    setError(null)
    try {
      const msgs = await listMessages(convId)
      setMessages(msgs)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [convId])

  useEffect(() => {
    setMessages([])
    refresh()
  }, [convId, refresh])

  const append = useCallback((msg: Message) => {
    setMessages((prev) => [...prev, msg])
  }, [])

  return { messages, loading, error, append, refresh }
}
