import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Typography,
} from '@mui/material'
import * as React from 'react'

import { IconArrowRight } from '@/components/icon'

export interface ICourseCardProps {
  courseInfo: {
    id: number
    title: string
    detailCourseUrl: string
    imgUrl: string
    description: string
  }
}

export default function CourseCard({
  courseInfo: { title, imgUrl, description },
}: ICourseCardProps) {
  return (
    <Card
      sx={{
        maxWidth: 500,
        borderRadius: '5px',
        backgroundColor: '#012233',
      }}
    >
      <CardActionArea>
        <CardMedia component="img" height="250" image={imgUrl} alt="image" />
        <CardContent
          sx={{
            backgroundColor: '#012233',
            borderRadius: '5px',
            padding: '20px 15px 25px 15px',
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
              {title}
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
              <Typography variant="body2" fontWeight={500}>
                Chi tiết
              </Typography>
              <IconArrowRight />
            </Box>
          </Box>

          <Typography variant="body2" mt={1}>
            {description}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
