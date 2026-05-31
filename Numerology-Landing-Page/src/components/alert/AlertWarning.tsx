import { Box } from '@mui/material'
import type { ReactNode } from 'react'

export interface IAlertWarningProps {
  children: ReactNode
}

export default function AlertWarning({ children }: IAlertWarningProps) {
  return (
    <Box
      sx={{
        py: 1.25,
        px: 2.5,
        display: 'inline-block',
        width: 'fit-content',
        color: (theme) => theme.palette.primary.main,
        borderRadius: '5px',
        border: (theme) => `1px solid ${theme.palette.primary.main}`,
        fontFeatureSettings: '"pnum" on, "lnum" on',
        cursor: 'default',
      }}
    >
      {children}
    </Box>
  )
}
