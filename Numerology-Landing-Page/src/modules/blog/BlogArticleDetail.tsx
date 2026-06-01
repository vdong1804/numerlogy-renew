/**
 * Blog article detail body.
 * Fetches a single news article by id and renders its HTML content
 * (sanitized with DOMPurify on the client to stay SSR-safe).
 */
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { Box, Button, Container, Divider, Typography } from '@mui/material'
import { useRouter } from 'next/router'
import { useEffect, useMemo, useState } from 'react'
import useSWR from 'swr'

import NotFound404 from '@/components/common/NotFound404'
import { SearchNumerologyForm } from '@/components/form'
import { Loading } from '@/components/loading'
import { BASE_URL } from '@/pages/api/axiosClient'
import numerologyApi from '@/pages/api/numerologyApi'

export default function BlogArticleDetail() {
  const router = useRouter()
  const id = router.query.id as string | undefined

  const { data, isLoading, error } = useSWR(
    id ? ['news-detail', id] : null,
    () => numerologyApi.getDetailNews(id as string)
  )

  // DOMPurify needs the DOM — load and run it only after mount.
  const [safeHtml, setSafeHtml] = useState('')
  useEffect(() => {
    let active = true
    if (!data?.content) {
      setSafeHtml('')
      return
    }
    import('dompurify').then(({ default: DOMPurify }) => {
      if (active) setSafeHtml(DOMPurify.sanitize(data.content))
    })
    return () => {
      active = false
    }
  }, [data?.content])

  const coverImage = useMemo(
    () => (data?.image ? `${BASE_URL}${data.image}` : null),
    [data?.image]
  )

  // Treat fetch error OR a resolved-but-empty article as not-found.
  if (error || (!isLoading && id && !data)) return <NotFound404 />

  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: 'calc(100vh - var(--header-height))',
        py: { xs: 4, md: 7 },
        background:
          'radial-gradient(circle at 12% 8%, rgba(249,106,45,0.16) 0%, transparent 45%),' +
          'radial-gradient(circle at 88% 92%, rgba(111,73,253,0.18) 0%, transparent 50%),' +
          'linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)',
        color: '#fff',
      }}
    >
      <Loading isOpen={isLoading} />
      <Container maxWidth="lg">
        <Button
          onClick={() => router.push('/blog')}
          startIcon={<ArrowBackIcon />}
          sx={{ color: 'rgba(255,255,255,0.8)', mb: 3 }}
        >
          Tất cả bài viết
        </Button>

        <Box display="flex" gap={5}>
          {/* Article */}
          <Box component="article" flex={1} minWidth={0}>
            <Typography
              component="h1"
              sx={{
                fontFamily: 'var(--philosopher-font)',
                fontWeight: 700,
                fontSize: { xs: '1.875rem', md: '2.5rem' },
                lineHeight: 1.2,
                mb: 3,
              }}
            >
              {data?.title || ''}
            </Typography>

            {coverImage && (
              <Box
                component="img"
                src={coverImage}
                alt={data?.title || 'Bài viết'}
                sx={{ width: '100%', borderRadius: '8px', mb: 3.5 }}
              />
            )}

            {/* Sanitized HTML content */}
            <Box
              className="blog-article-content"
              sx={{
                color: 'rgba(255,255,255,0.88)',
                lineHeight: 1.8,
                '& img': { maxWidth: '100%', height: 'auto', borderRadius: '8px', my: 2 },
                '& h2, & h3, & h4': {
                  fontFamily: 'var(--philosopher-font)',
                  fontWeight: 700,
                  color: '#fff',
                  mt: 3,
                  mb: 1.5,
                },
                '& p': { mb: 2 },
                '& a': { color: 'var(--primary, #F96A2D)' },
              }}
              dangerouslySetInnerHTML={{ __html: safeHtml }}
            />
          </Box>

          {/* Sidebar */}
          <Box
            width={'400px'}
            sx={{ display: { xs: 'none', lg: 'block' } }}
          >
            <SearchNumerologyForm title="Tra cứu chỉ số của bản thân ngay" />
            <Divider sx={{ my: 3.5, borderColor: 'rgba(255,255,255,0.12)' }} />
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
