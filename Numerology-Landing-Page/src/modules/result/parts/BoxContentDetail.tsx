import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { IconEyeOff } from '@/components/icon'

export interface IBoxContentDetailProps {
  title: ReactNode
  children?: ReactNode
  intro?: ReactNode
  isIconEyeOff?: boolean
}

export default function BoxContentDetail({
  title,
  children,
  intro,
  isIconEyeOff = false,
}: IBoxContentDetailProps) {
  return (
    <Box p={2.5} bgcolor={'#011625'} borderRadius={2.5}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Typography className="text-heading" component={'h3'} mr={1.25}>
          {title}
        </Typography>
        {isIconEyeOff && <IconEyeOff />}
      </Box>
      {intro && <Box mt={1.25}>{intro}</Box>}
      <Box mt={1.25}>{children}</Box>
    </Box>
  )
}
