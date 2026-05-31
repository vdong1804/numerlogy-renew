/**
 * Cloudflare Turnstile CAPTCHA widget.
 * Loads Turnstile script on mount and renders explicit challenge.
 * Dev fallback: if NEXT_PUBLIC_TURNSTILE_SITE_KEY is empty, calls onSuccess immediately.
 */
import { useEffect, useRef } from 'react'

interface TurnstileWidgetProps {
  onSuccess: (token: string) => void
  theme?: 'light' | 'dark'
}

// Global callback registry keyed by widget instance id
const CALLBACK_PREFIX = '__tsCallback_'

let widgetCounter = 0

export default function TurnstileWidget({ onSuccess, theme = 'light' }: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string>(`ts_${++widgetCounter}`)
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? ''

  useEffect(() => {
    // No site key configured: dev mode auto-passes, production blocks entirely.
    if (!siteKey) {
      if (process.env.NODE_ENV === 'production') {
        // Production misconfiguration — do NOT call onSuccess; let the error UI block submit.
        return
      }
      const timer = setTimeout(() => onSuccess('dev-skip-token'), 100)
      return () => clearTimeout(timer)
    }

    const callbackName = `${CALLBACK_PREFIX}${widgetIdRef.current}`

    // Register global callback that Turnstile will invoke
    ;(window as Record<string, unknown>)[callbackName] = (token: string) => {
      onSuccess(token)
    }

    const renderWidget = () => {
      if (!containerRef.current) return
      // Prevent double-render if already has children
      if (containerRef.current.childElementCount > 0) return

      const div = document.createElement('div')
      div.className = 'cf-turnstile'
      div.dataset.sitekey = siteKey
      div.dataset.callback = callbackName
      div.dataset.theme = theme
      containerRef.current.appendChild(div)

      // Ask Turnstile to render if already loaded
      if (typeof (window as Record<string, unknown>).turnstile !== 'undefined') {
        ;(window as { turnstile: { render: (el: HTMLElement) => void } }).turnstile.render(div)
      }
    }

    // Load Turnstile script if not already present
    const scriptId = 'cf-turnstile-script'
    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script')
      script.id = scriptId
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
      script.async = true
      script.defer = true
      script.onload = renderWidget
      document.head.appendChild(script)
    } else {
      renderWidget()
    }

    return () => {
      // Cleanup global callback
      delete (window as Record<string, unknown>)[callbackName]
    }
  }, [siteKey, theme, onSuccess])

  if (!siteKey) {
    if (process.env.NODE_ENV === 'production') {
      // Production build missing NEXT_PUBLIC_TURNSTILE_SITE_KEY — block form submission.
      return (
        <div
          style={{
            padding: '8px 12px',
            background: 'rgba(220,38,38,0.15)',
            borderRadius: 4,
            fontSize: 12,
            color: 'rgba(220,38,38,0.9)',
            border: '1px solid rgba(220,38,38,0.4)',
          }}
        >
          Captcha not configured — form submission disabled.
        </div>
      )
    }
    // Dev mode: show placeholder
    return (
      <div
        style={{
          padding: '8px 12px',
          background: 'rgba(255,255,255,0.08)',
          borderRadius: 4,
          fontSize: 12,
          color: 'rgba(255,255,255,0.5)',
        }}
      >
        [CAPTCHA disabled — dev mode]
      </div>
    )
  }

  return <div ref={containerRef} />
}
