/**
 * useConversations — list/create/delete conversations.
 * Plain useState + useEffect (no React Query in project).
 * TODO: migrate to React Query if added in future.
 */

import { useCallback, useEffect, useState } from 'react'

import type { Conversation } from '@/models/Chat'

import {
  createConversation,
  deleteConversation,
  listConversations,
} from '../api/chat-api'

interface UseConversationsReturn {
  conversations: Conversation[]
  loading: boolean
  error: string | null
  create: (title?: string) => Promise<Conversation>
  remove: (id: number) => Promise<void>
  refresh: () => Promise<void>
}

export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await listConversations()
      setConversations(list)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const create = useCallback(async (title?: string): Promise<Conversation> => {
    const conv = await createConversation(title)
    setConversations((prev) => [conv, ...prev])
    return conv
  }, [])

  const remove = useCallback(async (id: number): Promise<void> => {
    await deleteConversation(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
  }, [])

  return { conversations, loading, error, create, remove, refresh }
}
