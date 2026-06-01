import { Box, Typography } from '@mui/material'
import { useRouter } from 'next/router'

import type { NumerologyIndicator } from '@/models'

import IndicatorHtml from './parts/IndicatorHtml'

export interface NumberCardProps {
  /** Vietnamese display label, e.g. "Số Sứ Mệnh". */
  label: string
  indicator: NumerologyIndicator
  /** Free users: blur + show upsell hint over the interpretation. */
  isVip?: boolean
  /** Smaller variant used inside dense grids. */
  compact?: boolean
}

/**
 * Compact, reusable card: big glowing number + label + interpretation.
 * Works for any indicator (core numbers, peaks, challenges, personal cycle).
 */
export default function NumberCard({
  label,
  indicator,
  isVip = false,
  compact = false,
}: NumberCardProps) {
  const router = useRouter()
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

      <Box
        sx={{
          position: 'relative',
          ...(isVip
            ? {}
            : {
                maxHeight: 160,
                overflow: 'hidden',
                maskImage:
                  'linear-gradient(to bottom, #000 55%, transparent 100%)',
                WebkitMaskImage:
                  'linear-gradient(to bottom, #000 55%, transparent 100%)',
              }),
        }}
      >
        <IndicatorHtml html={indicator.content} sx={{ fontStyle: 'italic' }} />
      </Box>

      {!isVip && indicator.content && (
        <Typography
          component="span"
          onClick={() => router.push('/shop')}
          sx={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--text-main)',
            cursor: 'pointer',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          Nâng cấp VIP để xem đầy đủ luận giải →
        </Typography>
      )}
    </Box>
  )
}
