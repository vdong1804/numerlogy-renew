/**
 * Shared dark-themed layout for /login, /register, /forgot-password, /reset-password.
 * Wraps form content in a translucent card on a dark gradient background so
 * white-text MUI input overrides (theme default) remain legible.
 */
import { Box, Typography } from '@mui/material'
import Link from 'next/link'
import { useRouter } from 'next/router'
import type { ReactNode } from 'react'

interface AuthShellProps {
  title: string
  subtitle?: string
  children: ReactNode
}

export default function AuthShell({ title, subtitle, children }: AuthShellProps) {
  const router = useRouter()
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        // Match the public site's deep navy theme
        background:
          'radial-gradient(circle at 20% 10%, rgba(249,106,45,0.18) 0%, transparent 50%),' +
          'radial-gradient(circle at 80% 90%, rgba(111,73,253,0.18) 0%, transparent 55%),' +
          'linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)',
        py: { xs: 4, md: 8 },
        px: 2,
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: 480,
          p: { xs: 3, sm: 5 },
          borderRadius: 4,
          bgcolor: 'rgba(255, 255, 255, 0.06)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 18px 60px -20px rgba(0, 0, 0, 0.6)',
          color: '#fff',
        }}
      >
        <Box textAlign="center" mb={3}>
          <Link href="/" passHref legacyBehavior>
            <Box
              component="a"
              sx={{
                display: 'inline-block',
                mb: 2,
                opacity: 0.95,
                '&:hover': { opacity: 1 },
              }}
            >
              <img
                src={`${router.basePath}/numerology_logo.svg`}
                alt="Numerology"
                style={{ height: 36 }}
              />
            </Box>
          </Link>
          <Typography
            variant="h4"
            sx={{
              color: '#fff',
              fontWeight: 700,
              fontSize: '1.6rem',
              mb: 1,
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="body2"
              sx={{ color: 'rgba(255,255,255,0.7)' }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        {children}
      </Box>
    </Box>
  )
}
