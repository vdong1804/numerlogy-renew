/**
 * Analytics loader — GA4 + Meta Pixel.
 * Scripts only injected after user grants analytics/marketing consent.
 * Listens to nsq_consent_updated event to activate without page reload.
 */
import { useEffect } from 'react'

import { getConsent } from '@/lib/consent-storage'

const GA4_ID = process.env.NEXT_PUBLIC_GA4_ID ?? ''
const PIXEL_ID = process.env.NEXT_PUBLIC_FB_PIXEL_ID ?? ''

// Safely extend window for gtag / fbq
declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void
    fbq?: (...args: unknown[]) => void
    dataLayer?: unknown[]
    _fbq?: unknown
  }
}

function injectGA4() {
  if (!GA4_ID || document.getElementById('ga4-script')) return
  const s = document.createElement('script')
  s.id = 'ga4-script'
  s.src = `https://www.googletagmanager.com/gtag/js?id=${GA4_ID}`
  s.async = true
  document.head.appendChild(s)

  window.dataLayer = window.dataLayer ?? []
  window.gtag = function (...args: unknown[]) {
    window.dataLayer!.push(args)
  }
  window.gtag('js', new Date())
  window.gtag('config', GA4_ID, { send_page_view: false })
}

function injectPixel() {
  if (!PIXEL_ID || document.getElementById('fb-pixel-script')) return
  /* eslint-disable */
  const f = window
  const b = document
  const e = 'script'
  const v = 'https://connect.facebook.net/en_US/fbevents.js'
  if ((f as any).fbq) return
  const n: any = ((f as any).fbq = function () {
    n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments)
  })
  if (!(f as any)._fbq) (f as any)._fbq = n
  n.push = n
  n.loaded = true
  n.version = '2.0'
  n.queue = []
  const t = b.createElement(e) as HTMLScriptElement
  t.id = 'fb-pixel-script'
  t.async = true
  t.src = v
  const s = b.getElementsByTagName(e)[0]
  s.parentNode!.insertBefore(t, s)
  /* eslint-enable */
  window.fbq!('init', PIXEL_ID)
}

function activateConsented() {
  const consent = getConsent()
  if (consent?.analytics) injectGA4()
  if (consent?.marketing) injectPixel()
}

// --- Event helpers (call from any page/component) ---

export function trackPageView(url: string) {
  if (typeof window === 'undefined') return
  window.gtag?.('event', 'page_view', { page_path: url })
  window.fbq?.('track', 'PageView')
}

export function trackSignUp(method = 'email') {
  window.gtag?.('event', 'sign_up', { method })
  window.fbq?.('track', 'CompleteRegistration')
}

export function trackInitiateCheckout(orderId: string | number, value: number) {
  window.gtag?.('event', 'begin_checkout', { order_id: orderId, value, currency: 'VND' })
  window.fbq?.('track', 'InitiateCheckout', { value, currency: 'VND' })
}

export function trackPurchase(orderId: string | number, amount: number) {
  window.gtag?.('event', 'purchase', {
    transaction_id: String(orderId),
    value: amount,
    currency: 'VND',
  })
  window.fbq?.('track', 'Purchase', { value: amount, currency: 'VND' })
}

// --- Component ---

export default function Analytics() {
  useEffect(() => {
    // Activate on mount if consent already stored
    activateConsented()

    // Re-activate when user grants consent in cookie banner
    const handler = () => activateConsented()
    window.addEventListener('nsq_consent_updated', handler)
    return () => window.removeEventListener('nsq_consent_updated', handler)
  }, [])

  return null
}
