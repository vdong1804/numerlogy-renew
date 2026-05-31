/**
 * Sentry browser-side config.
 * DSN must use NEXT_PUBLIC_ prefix to be exposed to browser bundles.
 * Docs: https://docs.sentry.io/platforms/javascript/guides/nextjs/
 */
import * as Sentry from '@sentry/nextjs'

// Regex patterns for PII scrubbing
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
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Sample 10% of transactions — adjust post-launch based on volume
  tracesSampleRate: 0.1,

  // Sample 10% of replays (session replay, if enabled)
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  environment: process.env.NEXT_PUBLIC_ENV ?? 'production',

  // Only enable in production-like envs to avoid noise during dev
  enabled: process.env.NODE_ENV === 'production',

  beforeSend(event) {
    // Strip PII from message
    if (event.message) {
      event.message = scrubString(event.message) as string
    }

    // Strip PII from exception values
    if (event.exception?.values) {
      for (const ex of event.exception.values) {
        if (ex.value) ex.value = scrubString(ex.value) as string
      }
    }

    // Strip PII from request body / data
    if (event.request?.data && typeof event.request.data === 'string') {
      event.request.data = scrubString(event.request.data) as string
    }

    // Strip Authorization header
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
