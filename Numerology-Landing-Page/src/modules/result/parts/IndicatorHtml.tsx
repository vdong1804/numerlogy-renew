import { Box } from '@mui/material'
import { useEffect, useState } from 'react'

export interface IndicatorHtmlProps {
  /** Raw HTML string from the backend (may be null). */
  html?: string | null
  /** Optional sx applied to the wrapper. */
  sx?: object
}

/**
 * Renders backend HTML safely: DOMPurify runs only after mount so SSR stays
 * clean. Returns null when there is nothing to show. DRY helper reused by
 * every report section.
 */
export default function IndicatorHtml({ html, sx }: IndicatorHtmlProps) {
  const [safeHtml, setSafeHtml] = useState('')

  useEffect(() => {
    let active = true
    if (!html) {
      setSafeHtml('')
      return
    }
    import('dompurify').then(({ default: DOMPurify }) => {
      if (active) setSafeHtml(DOMPurify.sanitize(html))
    })
    return () => {
      active = false
    }
  }, [html])

  if (!html) return null
  return (
    <Box
      className="indicator-html"
      sx={{ '& p': { mb: 1.25 }, ...sx }}
      dangerouslySetInnerHTML={{ __html: safeHtml }}
    />
  )
}
