/**
 * useQuota — fetches /api/chat/quota on mount and exposes refresh().
 * Refresh is called: after each successful send, after a successful purchase.
 * No polling in v1 — event-driven only (KISS).
 */

import { useCallback, useEffect, useState } from 'react'

import type { Quota } from '@/models/Chat'

import { getQuota } from '../api/chat-api'

interface UseQuotaReturn {
  quota: Quota | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useQuota(): UseQuotaReturn {
  const [quota, setQuota] = useState<Quota | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setError(null)
      const data = await getQuota()
      setQuota(data)
    } catch (err) {
      setError((err as Error).message || 'Không tải được hạn mức')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { quota, loading, error, refresh }
}
