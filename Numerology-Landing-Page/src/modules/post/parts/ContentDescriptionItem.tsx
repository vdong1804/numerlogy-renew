import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

export interface IContentDescriptionItemProps {
  title: ReactNode
  children: ReactNode
}

export default function ContentDescriptionItem({
  title,
  children,
}: IContentDescriptionItemProps) {
  return (
    <Box>
      <Typography component="h3" className="text-heading">
        {title}
      </Typography>
      <Box mt={2.5}>
        <Box display={'flex'} flexDirection={'column'} rowGap={'15px'}>
          {children}
        </Box>
      </Box>
    </Box>
  )
}
