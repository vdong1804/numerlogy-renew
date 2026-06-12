import { Box, Typography } from '@mui/material'
import { useRouter } from 'next/router'

import { IconEyeOff } from '@/components/icon'

export interface LockOverlayProps {
  /** Short teaser/label shown above the unlock CTA. */
  hint?: string
}

/**
 * Placeholder shown in place of a locked interpretation. The paid content is
 * never sent to the client (stripped server-side), so this is a genuine gate —
 * not a CSS blur over real text. Clicking routes to the shop to unlock.
 */
export default function LockOverlay({
  hint = 'Nội dung này dành cho báo cáo đầy đủ',
}: LockOverlayProps) {
  const router = useRouter()
  return (
    <Box
      onClick={() => router.push('/shop')}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        rowGap: 1,
        textAlign: 'center',
        py: 2.5,
        px: 1.5,
        borderRadius: 2,
        cursor: 'pointer',
        border: '1px dashed rgba(68, 187, 255, 0.35)',
        backgroundColor: 'rgba(0, 168, 255, 0.05)',
        transition: 'background-color .2s ease',
        '&:hover': { backgroundColor: 'rgba(0, 168, 255, 0.1)' },
      }}
    >
      <IconEyeOff />
      <Typography variant="body2" sx={{ fontStyle: 'italic', opacity: 0.85 }}>
        {hint}
      </Typography>
      <Typography
        component="span"
        sx={{
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: 'var(--text-main)',
          '&:hover': { textDecoration: 'underline' },
        }}
      >
        Mở khóa báo cáo đầy đủ →
      </Typography>
    </Box>
  )
}
