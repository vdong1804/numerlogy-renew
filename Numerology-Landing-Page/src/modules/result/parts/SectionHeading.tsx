import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

export interface SectionHeadingProps {
  title: string
  subtitle?: ReactNode
}

/**
 * Centered section heading with the cosmic accent underline. Reused by every
 * grouped section (core numbers, peaks, challenges, ...).
 */
export default function SectionHeading({ title, subtitle }: SectionHeadingProps) {
  return (
    <Box textAlign="center" mb={1.25}>
      <Typography className="text-heading" component="h2" margin="0 auto">
        {title}
      </Typography>
      <Box
        sx={{
          width: 64,
          height: 3,
          mx: 'auto',
          mt: 1,
          borderRadius: 2,
          background:
            'linear-gradient(90deg, transparent, var(--text-main), transparent)',
        }}
      />
      {subtitle && (
        <Typography mt={1.25} fontStyle="italic" sx={{ opacity: 0.85 }}>
          {subtitle}
        </Typography>
      )}
    </Box>
  )
}
