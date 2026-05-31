/**
 * LegalDocument — typography wrapper for legal/policy pages.
 *
 * Provides consistent heading + list + table styling on the dark themed
 * PageShell so legal text feels integrated with the home page design.
 *
 * Use inside <PageShell bare={false}> for a glass card around the text.
 */
import { Box } from '@mui/material'
import type { ReactNode } from 'react'

interface LegalDocumentProps {
  children: ReactNode
}

export default function LegalDocument({ children }: LegalDocumentProps) {
  return (
    <Box
      sx={{
        color: 'rgba(255,255,255,0.88)',
        lineHeight: 1.8,
        fontSize: '0.95rem',
        '& h2': {
          fontFamily: 'var(--philosopher-font)',
          fontSize: { xs: '1.25rem', md: '1.5rem' },
          fontWeight: 700,
          color: '#fff',
          mt: 4,
          mb: 1.5,
          position: 'relative',
          pl: 2,
          '&::before': {
            content: '""',
            position: 'absolute',
            left: 0,
            top: '0.25em',
            bottom: '0.25em',
            width: 3,
            borderRadius: 999,
            bgcolor: '#F96A2D',
          },
        },
        '& h2:first-of-type': { mt: 0 },
        '& h3': {
          fontFamily: 'var(--philosopher-font)',
          fontSize: '1.1rem',
          fontWeight: 700,
          color: '#fff',
          mt: 3,
          mb: 1,
        },
        '& p': { mb: 1.5 },
        '& strong': { color: '#fff' },
        '& a': {
          color: '#F96A2D',
          textDecoration: 'underline',
          textUnderlineOffset: 2,
          '&:hover': { color: '#FF8A52' },
        },
        '& ul, & ol': {
          pl: 3,
          mb: 1.5,
          '& li': { mb: 0.75 },
        },
        '& table': {
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.9rem',
          my: 2,
          borderRadius: 2,
          overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.12)',
        },
        '& thead': {
          bgcolor: 'rgba(249,106,45,0.12)',
        },
        '& th': {
          padding: '10px 14px',
          textAlign: 'left',
          fontWeight: 600,
          color: '#fff',
          borderBottom: '1px solid rgba(255,255,255,0.15)',
        },
        '& td': {
          padding: '10px 14px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          verticalAlign: 'top',
          color: 'rgba(255,255,255,0.85)',
        },
        '& tr:last-child td': { borderBottom: 'none' },
        '& section + section': { mt: 1 },
      }}
    >
      {children}
    </Box>
  )
}
