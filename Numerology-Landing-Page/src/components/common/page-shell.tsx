/**
 * PageShell — dark cosmic wrapper for static/legal/help pages.
 * Matches the home page design language:
 *   - Deep navy gradient with warm orange + violet halos
 *   - Translucent glass card content area
 *   - Philosopher heading + orange accent bar
 *
 * Use this to wrap static content (legal, FAQ, guide, contact) so it
 * feels consistent with the home page hero/sections.
 */
import { Box, Container, Typography } from '@mui/material'
import type { ReactNode } from 'react'

interface PageShellProps {
  title: string
  subtitle?: ReactNode
  /** When true, render content directly without the glass card frame. */
  bare?: boolean
  /** Container max width — defaults to "md" for legal/help pages. */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false
  children: ReactNode
}

export default function PageShell({
  title,
  subtitle,
  bare = false,
  maxWidth = 'md',
  children,
}: PageShellProps) {
  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: 'calc(100vh - var(--header-height))',
        py: { xs: 5, md: 8 },
        px: 2,
        background:
          'radial-gradient(circle at 12% 8%, rgba(249,106,45,0.16) 0%, transparent 45%),' +
          'radial-gradient(circle at 88% 92%, rgba(111,73,253,0.18) 0%, transparent 50%),' +
          'linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)',
        color: '#fff',
        overflow: 'hidden',
      }}
    >
      <Container maxWidth={maxWidth}>
        {/* Hero heading */}
        <Box textAlign="center" mb={{ xs: 4, md: 6 }}>
          <Typography
            component="h1"
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontWeight: 700,
              fontSize: { xs: '2rem', md: '2.75rem' },
              lineHeight: 1.15,
              mb: 1.5,
              color: '#fff',
            }}
          >
            {title}
          </Typography>
          <Box
            sx={{
              width: 64,
              height: 3,
              bgcolor: '#F96A2D',
              borderRadius: 999,
              mx: 'auto',
              mb: subtitle ? 2.5 : 0,
            }}
          />
          {subtitle && (
            <Typography
              sx={{
                color: 'rgba(255,255,255,0.78)',
                fontSize: { xs: '0.95rem', md: '1.0625rem' },
                maxWidth: 640,
                mx: 'auto',
                lineHeight: 1.6,
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>

        {bare ? (
          children
        ) : (
          <Box
            sx={{
              borderRadius: 4,
              p: { xs: 2.5, md: 5 },
              bgcolor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.10)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 20px 60px -20px rgba(0,0,0,0.45)',
              color: '#fff',
            }}
          >
            {children}
          </Box>
        )}
      </Container>
    </Box>
  )
}
