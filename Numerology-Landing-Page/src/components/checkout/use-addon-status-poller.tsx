/**
 * useAddonStatusPoller — polls /api/chat/quota every `intervalMs` to detect
 * when a chat add-on purchase has been fulfilled by the SePay webhook.
 *
 * Returns a `SePayStatus` consumable by SePayPaymentBlock:
 *   - 'pending' while still waiting
 *   - 'paid'    when quota.addonRemaining > startingRemaining
 *   - 'expired' after `timeoutMs` without fulfilment
 *
 * Caller passes the user's quota snapshot BEFORE initiating purchase via
 * `startingAddonRemaining` so the hook detects any positive delta — robust
 * against pre-existing add-on credit.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { getQuota } from '@/modules/chat/api/chat-api'

import type { SePayStatus } from './sepay-payment-block'

interface UseAddonStatusPollerOpts {
  /** Only poll when true — toggle off when bank info is hidden */
  enabled: boolean
  /** addonRemaining snapshot just before purchase. Hook fires `paid` on any positive delta. */
  startingAddonRemaining: number
  intervalMs?: number
  /** Total wait window (default 5 min, matches legacy behaviour) */
  timeoutMs?: number
  /** Called once when status transitions to `paid` */
  onPaid?: () => void
}

export default function useAddonStatusPoller({
  enabled,
  startingAddonRemaining,
  intervalMs = 8000,
  timeoutMs = 5 * 60 * 1000,
  onPaid,
}: UseAddonStatusPollerOpts) {
  const [status, setStatus] = useState<SePayStatus>('pending')
  const firedRef = useRef(false)
  const startedAtRef = useRef<number>(Date.now())

  // Re-arm whenever enabled flips to true (e.g. new purchase initiated).
  useEffect(() => {
    if (enabled) {
      firedRef.current = false
      startedAtRef.current = Date.now()
      setStatus('pending')
    }
  }, [enabled])

  const tick = useCallback(async () => {
    try {
      const q = await getQuota()
      if (q.addonRemaining > startingAddonRemaining && !firedRef.current) {
        firedRef.current = true
        setStatus('paid')
        onPaid?.()
      }
    } catch {
      // transient errors — keep polling
    }
  }, [startingAddonRemaining, onPaid])

  useEffect(() => {
    if (!enabled || status !== 'pending') return undefined
    const id = window.setInterval(() => {
      if (Date.now() - startedAtRef.current >= timeoutMs) {
        setStatus('expired')
        window.clearInterval(id)
        return
      }
      tick()
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [enabled, status, intervalMs, timeoutMs, tick])

  return { status }
}
