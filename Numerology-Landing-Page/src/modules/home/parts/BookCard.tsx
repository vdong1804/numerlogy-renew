import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Typography,
} from '@mui/material'
import * as React from 'react'

interface BookCardProps {
  bookInfo: {
    imgUrl: string
    name: string
    isActive: boolean
  }
}
export default function BookCard({
  bookInfo: { imgUrl, name, isActive },
}: BookCardProps) {
  return (
    <Box maxWidth={295}>
      <Card sx={{ width: '100%', backgroundColor: 'transparent' }}>
        <CardActionArea>
          <CardMedia
            component="img"
            height="427"
            image={imgUrl}
            alt="image"
            className={!isActive ? 'grayscale' : ''}
          />
        </CardActionArea>
      </Card>
      <CardContent sx={{ paddingTop: 2.5, textAlign: 'center' }}>
        <Typography
          className="line-clamp-2"
          variant="h4"
          component="h4"
          sx={{
            fontFamily: 'var(--philosopher-font)',
            width: '172px',
            margin: '0 auto',
          }}
        >
          {name}
        </Typography>
        <Button
          variant={isActive ? 'contained' : 'outlined'}
          color="primary"
          sx={{ marginTop: 2.5 }}
        >
          Tìm hiểu thêm
        </Button>
      </CardContent>
    </Box>
  )
}
