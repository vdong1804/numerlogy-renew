/**
 * Sentry server-side config (Node.js runtime).
 * Server-side can use SENTRY_DSN (not exposed to browser).
 */
import * as Sentry from '@sentry/nextjs'

const EMAIL_RE = /[\w.+-]+@[\w-]+\.[\w.-]+/gi
const PHONE_RE = /(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}/g
const JWT_RE = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g

function scrubString(s: unknown): string | unknown {
  if (typeof s !== 'string') return s
  return s
    .replace(EMAIL_RE, '[email]')
    .replace(PHONE_RE, '[phone]')
    .replace(JWT_RE, '[jwt]')
}

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NEXT_PUBLIC_ENV ?? 'production',
  enabled: process.env.NODE_ENV === 'production',

  beforeSend(event) {
    if (event.message) {
      event.message = scrubString(event.message) as string
    }
    if (event.exception?.values) {
      for (const ex of event.exception.values) {
        if (ex.value) ex.value = scrubString(ex.value) as string
      }
    }
    if (event.request?.data && typeof event.request.data === 'string') {
      event.request.data = scrubString(event.request.data) as string
    }
    if (event.request?.headers) {
      const headers = event.request.headers as Record<string, string>
      if (headers['Authorization'] || headers['authorization']) {
        headers['Authorization'] = '[filtered]'
        headers['authorization'] = '[filtered]'
      }
    }
    return event
  },
})
