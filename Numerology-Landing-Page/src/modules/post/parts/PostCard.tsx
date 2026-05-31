import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Typography,
} from '@mui/material'

import { IconArrowRight } from '@/components/icon'

interface PostCardProps {
  postInfo: {
    title: string
    imgLink: string
    to: string
  }
}
export default function PostCard({
  postInfo: { title, imgLink, to },
}: PostCardProps) {
  return (
    <Card
      sx={{
        maxWidth: 500,
        borderRadius: '5px',
        backgroundColor: 'transparent',
        boxShadow: 'none',
      }}
    >
      <CardActionArea
        sx={{ display: 'flex', columnGap: 2.5, alignItems: 'flex-start' }}
      >
        <CardMedia
          component="img"
          sx={{ width: 118, height: 98, flexShrink: 0, borderRadius: '5px' }}
          image={imgLink}
          alt="Post Image"
        />
        <CardContent
          sx={{
            p: 0,
            color: 'common.white',
            alignSelf: 'stretch',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Typography
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontSize: '1.125rem',
              fontWeight: 700,
              lineHeight: 1.4,
            }}
            className="line-clamp-3"
          >
            {title}
          </Typography>
          <Box
            sx={{
              mt: 'auto',
              color: 'common.white',
              cursor: 'pointer',
              display: 'flex',
              columnGap: 1,
              alignItems: 'center',
              '&:hover': {
                filter: 'brightness(0.7)',
              },
            }}
            component={'a'}
            href={to}
          >
            <Typography variant="body2" fontWeight={500} lineHeight={'20px'}>
              Chi tiết
            </Typography>
            <IconArrowRight />
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
