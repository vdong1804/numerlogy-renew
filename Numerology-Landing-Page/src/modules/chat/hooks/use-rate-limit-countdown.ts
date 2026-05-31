/**
 * useRateLimitCountdown — tracks a server-driven rate-limit cooldown period.
 * Exposes active/secondsLeft state + trigger/clear controls.
 * Used by ChatLayout to disable MessageInput while the bucket refills.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export interface RateLimitState {
  active: boolean
  secondsLeft: number
  reason: 'bucket_empty' | 'daily_cap' | null
}

export interface UseRateLimitCountdownReturn extends RateLimitState {
  /** Start countdown. If retryAfter is 0, no-op. */
  trigger: (retryAfter: number, reason: 'bucket_empty' | 'daily_cap') => void
  /** Cancel countdown immediately (e.g., after successful send). */
  clear: () => void
}

export function useRateLimitCountdown(): UseRateLimitCountdownReturn {
  const [state, setState] = useState<RateLimitState>({
    active: false,
    secondsLeft: 0,
    reason: null,
  })
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopInterval = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const clear = useCallback(() => {
    stopInterval()
    setState({ active: false, secondsLeft: 0, reason: null })
  }, [stopInterval])

  const trigger = useCallback(
    (retryAfter: number, reason: 'bucket_empty' | 'daily_cap') => {
      if (retryAfter <= 0) return
      stopInterval()
      setState({ active: true, secondsLeft: retryAfter, reason })

      intervalRef.current = setInterval(() => {
        setState((prev) => {
          const next = prev.secondsLeft - 1
          if (next <= 0) {
            // Clear interval immediately inside the updater to avoid a
            // redundant tick between setState and the effect cleanup.
            stopInterval()
            return { active: false, secondsLeft: 0, reason: null }
          }
          return { ...prev, secondsLeft: next }
        })
      }, 1000)
    },
    [stopInterval]
  )

  // Fallback: stop interval if active flips to false via clear() or external reset
  useEffect(() => {
    if (!state.active && intervalRef.current !== null) {
      stopInterval()
    }
  }, [state.active, stopInterval])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopInterval()
    }
  }, [stopInterval])

  return { ...state, trigger, clear }
}
