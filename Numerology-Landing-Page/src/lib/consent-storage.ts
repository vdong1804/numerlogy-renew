/**
 * Consent state persistence — localStorage key "nsq_consent_v1"
 * Compliant with NĐ 13/2023: analytics/marketing blocked until explicit accept.
 */

export interface ConsentState {
  analytics: boolean
  marketing: boolean
  timestamp: number
}

const STORAGE_KEY = 'nsq_consent_v1'
const EXPIRE_MS = 365 * 24 * 60 * 60 * 1000 // 365 days

export function getConsent(): ConsentState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed: ConsentState = JSON.parse(raw)
    // Expire after 365 days
    if (Date.now() - parsed.timestamp > EXPIRE_MS) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function setConsent(state: Omit<ConsentState, 'timestamp'>): ConsentState {
  const full: ConsentState = { ...state, timestamp: Date.now() }
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(full))
  }
  return full
}

export function clearConsent(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY)
  }
}

export function hasValidConsent(): boolean {
  return getConsent() !== null
}
