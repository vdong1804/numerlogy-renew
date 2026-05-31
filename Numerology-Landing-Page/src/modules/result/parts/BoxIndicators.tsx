import { Box, Divider, Typography } from '@mui/material'
import * as React from 'react'

import { IconEyeOff } from '@/components/icon'

export interface BoxIndicatorsProps {
  title: string
}

export default function BoxIndicators({ title }: BoxIndicatorsProps) {
  return (
    <Box
      sx={{
        width: 305,
        height: 44,
        display: 'flex',
        alignItems: 'center',
        bgcolor: 'rgba(255, 255, 255, 0.11)',
        border: '1px solid #FAFAFA',
        margin: '0 auto',
      }}
    >
      <Typography
        component={'span'}
        fontWeight={700}
        textAlign={'center'}
        width={'60%'}
      >
        {title}
      </Typography>
      <Divider
        orientation="vertical"
        variant="fullWidth"
        sx={{ borderColor: '#FAFAFA' }}
        flexItem
      />
      <Box
        flex={1}
        display={'flex'}
        justifyContent={'center'}
        alignItems={'center'}
      >
        <IconEyeOff />
      </Box>
    </Box>
  )
}
