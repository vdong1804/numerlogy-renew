/**
 * News-style article card for the blog list grid.
 * Shows cover image, title and a short content preview.
 */
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

export interface BlogArticleCardProps {
  article: News
}

const FALLBACK_IMG = '/assets/images/bg-blog-numberology.png'

export default function BlogArticleCard({ article }: BlogArticleCardProps) {
  const router = useRouter()
  const preview =
    article.content_preview || article.short_content || ''
  const image = article.image
    ? `${BASE_URL}${article.image}`
    : FALLBACK_IMG

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '8px',
        backgroundColor: 'rgba(2, 39, 59, 0.8)',
        border: '1px solid #0E263B',
        transition: 'transform 0.2s ease, border-color 0.2s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          borderColor: 'var(--primary, #F96A2D)',
        },
      }}
    >
      <CardActionArea
        onClick={() => router.push(`/blog/${article.id}`)}
        sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
      >
        <CardMedia
          component="img"
          height="200"
          image={image}
          alt={article.title}
        />
        <CardContent
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            color: '#fff',
            p: 2.5,
          }}
        >
          <Typography
            component="h3"
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontSize: '1.25rem',
              fontWeight: 700,
              lineHeight: 1.3,
              mb: 1,
            }}
            className="line-clamp-2"
          >
            {article.title}
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: 'rgba(255,255,255,0.75)', flex: 1 }}
            className="line-clamp-3"
          >
            {preview}
          </Typography>
          <Box
            sx={{
              mt: 2,
              display: 'flex',
              alignItems: 'center',
              columnGap: 1,
              color: 'var(--primary, #F96A2D)',
            }}
          >
            <Typography variant="body2" fontWeight={600}>
              Đọc tiếp
            </Typography>
            <IconArrowRight />
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
