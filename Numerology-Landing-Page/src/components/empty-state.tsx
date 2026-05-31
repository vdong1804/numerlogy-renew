/**
 * Generic empty state component.
 * Shows an icon, title, description, and optional CTA button.
 */
import { Box, Button, Typography } from '@mui/material'
import Link from 'next/link'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: string
  ctaLabel?: string
  ctaHref?: string
}

export default function EmptyState({
  icon,
  title,
  description,
  ctaLabel,
  ctaHref,
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        py: 8,
        px: 2,
        gap: 2,
      }}
    >
      <Box sx={{ fontSize: 56, color: 'text.disabled', lineHeight: 1 }}>{icon}</Box>

      <Typography variant="h6" fontWeight={600}>
        {title}
      </Typography>

      {description && (
        <Typography variant="body2" color="text.secondary" maxWidth={360}>
          {description}
        </Typography>
      )}

      {ctaLabel && ctaHref && (
        <Link href={ctaHref} passHref legacyBehavior>
          <Button
            component="a"
            variant="contained"
            color="primary"
            sx={{ mt: 1, px: 4, py: 1.2 }}
          >
            {ctaLabel}
          </Button>
        </Link>
      )}
    </Box>
  )
}
