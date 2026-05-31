import { Avatar, Box, Typography } from '@mui/material'
import * as React from 'react'

import { IconComment } from '@/components/icon'

export interface IBoxCommentProps {
  user: {
    id: number
    name: string
    job: string
    avatar: string
  }
  content: string
}

export default function BoxComment({
  user: { name, job, avatar },
  content,
}: IBoxCommentProps) {
  return (
    <Box>
      <Box
        p={2.5}
        paddingBottom={7}
        bgcolor={'#031D2E'}
        boxShadow={'0px 4px 20px rgba(1, 8, 12, 0.41)'}
        maxWidth={'327px'}
        position={'relative'}
        margin={'0 auto'}
      >
        <Box textAlign={'center'}>
          <IconComment />
        </Box>
        <Typography mt={1} textAlign={'center'} lineHeight={'20px'}>
          {content}
        </Typography>
      </Box>
      <Box
        sx={{
          position: 'relative',
          left: '50%',
          transform: 'translateX(-50%)',
          mt: '-32px',
          textAlign: 'center',
          width: 'fit-content',
          display: 'inline-block',
          borderRadius: '5px',
        }}
      >
        <Avatar
          alt="Avatar user"
          src={avatar}
          sx={{ width: '65px', height: '65px', margin: '0 auto' }}
        />
        <Typography
          sx={{
            fontFamily: 'var(--philosopher-font)',
            fontSize: 20,
            lineHeight: 1,
            fontWeight: 700,
            marginTop: 1,
            textAlign: 'center',
          }}
        >
          {name}
        </Typography>
        <Typography
          sx={{
            fontSize: 14,
            fontStyle: 'italic',
            marginTop: 0.5,
            textAlign: 'center',
          }}
        >
          {job}
        </Typography>
      </Box>
    </Box>
  )
}
