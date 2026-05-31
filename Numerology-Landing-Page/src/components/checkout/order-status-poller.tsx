/**
 * useOrderStatusPoller — react hook that polls /api/orders/:id/status.
 *
 * - Polls every `intervalMs` (default 3s) while status === 'pending'.
 * - Auto-stops on terminal status (paid / expired / cancelled / failed).
 * - Auto-stops after `timeoutMs` (default 30 min, matches server expiry).
 * - Returns latest status + manual `refresh` and `stopped` flag.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { getOrderStatus, type OrderStatusInfo } from '@/lib/shop-api'

interface UseOrderStatusPollerOpts {
  orderId: number
  initialStatus?: OrderStatusInfo['status']
  intervalMs?: number
  timeoutMs?: number
  /** Called once when status transitions away from 'pending'. */
  onResolved?: (info: OrderStatusInfo) => void
}

const TERMINAL = new Set<OrderStatusInfo['status']>([
  'paid',
  'expired',
  'cancelled',
  'failed',
])

export default function useOrderStatusPoller({
  orderId,
  initialStatus = 'pending',
  intervalMs = 3000,
  timeoutMs = 30 * 60 * 1000,
  onResolved,
}: UseOrderStatusPollerOpts) {
  const [status, setStatus] = useState<OrderStatusInfo['status']>(initialStatus)
  const [paidAt, setPaidAt] = useState<string | null | undefined>(null)
  const [error, setError] = useState<string | null>(null)
  const [stopped, setStopped] = useState(false)

  const resolvedFiredRef = useRef(false)
  const startedAtRef = useRef<number>(Date.now())

  const tick = useCallback(async () => {
    try {
      const info = await getOrderStatus(orderId)
      setStatus(info.status)
      setPaidAt(info.paid_at ?? null)
      if (TERMINAL.has(info.status) && !resolvedFiredRef.current) {
        resolvedFiredRef.current = true
        onResolved?.(info)
        setStopped(true)
      }
    } catch (err) {
      setError((err as Error).message)
    }
  }, [orderId, onResolved])

  useEffect(() => {
    if (TERMINAL.has(status)) {
      setStopped(true)
      return
    }
    const id = window.setInterval(() => {
      if (Date.now() - startedAtRef.current >= timeoutMs) {
        setStopped(true)
        window.clearInterval(id)
        return
      }
      tick()
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [tick, intervalMs, timeoutMs, status])

  return { status, paidAt, error, stopped, refresh: tick }
}
