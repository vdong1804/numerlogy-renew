import { Box, Typography } from '@mui/material'

import type { NumerologyIndicator } from '@/models'

import IndicatorHtml from './parts/IndicatorHtml'
import LockOverlay from './parts/LockOverlay'

export interface NumberCardProps {
  /** Vietnamese display label, e.g. "Số Sứ Mệnh". */
  label: string
  indicator: NumerologyIndicator
  /** Smaller variant used inside dense grids. */
  compact?: boolean
}

/**
 * Compact, reusable card: big glowing number + label + interpretation.
 * Works for any indicator (core numbers, peaks, challenges, personal cycle).
 *
 * Gating is server-driven: when `indicator.locked` the backend has stripped the
 * interpretation, so we render a real lock overlay (not a CSS blur over content).
 */
export default function NumberCard({
  label,
  indicator,
  compact = false,
}: NumberCardProps) {
  // Guard against a missing indicator (e.g. an API payload that omits a field)
  // so one absent number never crashes the whole result page.
  if (!indicator) return null
  return (
    <Box
      p={2.5}
      bgcolor="#011625"
      borderRadius={2.5}
      height="100%"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        rowGap: 1.25,
        border: '1px solid rgba(68, 187, 255, 0.12)',
        backdropFilter: 'blur(6px)',
        transition: 'transform .2s ease, box-shadow .2s ease',
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: '0 10px 30px rgba(27, 90, 251, 0.18)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', columnGap: 1.5 }}>
        <Typography
          component="span"
          sx={{
            fontSize: compact ? '2.25rem' : '2.75rem',
            fontWeight: 700,
            lineHeight: 1,
            color: '#44BBFF',
            textShadow: '0px 4px 13px rgba(27, 90, 251, 0.6)',
          }}
        >
          {indicator.code}
        </Typography>
        <Typography
          className="text-heading-secondary"
          component="h3"
          sx={{ width: 'auto' }}
        >
          {label}
        </Typography>
      </Box>

      {indicator.locked ? (
        <LockOverlay hint={`Luận giải ${label} dành cho báo cáo đầy đủ`} />
      ) : (
        <IndicatorHtml html={indicator.content} sx={{ fontStyle: 'italic' }} />
      )}
    </Box>
  )
}
