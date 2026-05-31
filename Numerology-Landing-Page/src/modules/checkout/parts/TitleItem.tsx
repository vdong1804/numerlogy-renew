import { Typography } from '@mui/material'
import type { ReactNode } from 'react'

export interface TitleItemProps {
  children: ReactNode
}

export default function TitleItem({ children }: TitleItemProps) {
  return (
    <Typography component={'h4'} color="grey.600" fontWeight={'600'} mb={1.25}>
      {children}
    </Typography>
  )
}
