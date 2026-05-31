import { Box } from '@mui/material'
import clsx from 'clsx'
import type { ReactNode } from 'react'

interface ButtonBankProps {
  children: ReactNode
  isActive?: boolean
}

export default function ButtonBank({
  children,
  isActive = false,
}: ButtonBankProps) {
  return (
    <Box
      className={clsx(!isActive && 'grayscale')}
      sx={{
        bgcolor: 'common.white',
        border: (theme) =>
          `1px solid ${isActive ? '#2979FF' : theme.palette.grey[100]}`,
        borderRadius: 2,
        maxWidth: 180,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        cursor: 'pointer',
        boxShadow: 1,
        transition: 'all ease 0.2s',
        '&:hover': {
          filter: 'brightness(0.9)',
          borderColor: '#2979FF',
        },
      }}
    >
      {children}
    </Box>
  )
}
