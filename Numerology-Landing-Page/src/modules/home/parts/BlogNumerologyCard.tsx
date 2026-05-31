import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Typography,
} from '@mui/material'
import { useRouter } from 'next/router'

import { IconArrowRight } from '@/components/icon'
import type { News } from '@/models'
import { BASE_URL } from '@/pages/api/axiosClient'

export interface BlogNumerologyCardProps {
  newsInfo: News
}

export default function BlogNumerologyCard({
  newsInfo,
}: BlogNumerologyCardProps) {
  const router = useRouter()
  return (
    <Card
      sx={{
        width: '100%',
        maxWidth: '295px',
        minWidth: '275px',
        borderRadius: '5px',
        position: 'relative',
        backgroundColor: 'rgba(2, 39, 59, 0.8)',
        margin: '0 auto',
      }}
    >
      <CardActionArea>
        <CardMedia
          component="img"
          alt="image"
          height="422"
          image={`${BASE_URL + newsInfo.image}`}
        />
        <CardContent
          sx={{
            position: 'absolute',
            bottom: 0,
            backgroundColor: 'rgba(2, 39, 59, 0.8)',
            borderRadius: '5px',
            padding: '15px 10px 20px 10px',
            color: '#fff',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              columnGap: 3,
              alignItems: 'start',
            }}
          >
            <Typography
              component="h4"
              variant="h4"
              sx={{
                fontFamily: 'var(--philosopher-font)',
                lineHeight: '20px',
              }}
            >
              {newsInfo.title}
            </Typography>
            <Box
              sx={{
                cursor: 'pointer',
                display: 'flex',
                flexShrink: 0,
                columnGap: 1,
                alignItems: 'center',
                '&:hover': {
                  filter: 'brightness(0.7)',
                },
              }}
            >
              <Typography
                variant="body2"
                fontWeight={500}
                lineHeight={'20px'}
                onClick={() => router.push(`/post/${newsInfo.id}`)}
              >
                Chi tiết
              </Typography>
              <IconArrowRight />
            </Box>
          </Box>

          <Typography variant="body2" mt={1}>
            {newsInfo.content}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
