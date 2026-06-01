/**
 * Blog list page body — news-style grid of numerology articles.
 * Fetches the paginated /api/news list with "load more" pagination.
 */
import { Box, Button, Container, Grid, Typography } from '@mui/material'
import { useMemo } from 'react'
import useSWRInfinite from 'swr/infinite'

import { IconTwoRhombus } from '@/components/icon'
import { Loading } from '@/components/loading'
import numerologyApi from '@/pages/api/numerologyApi'

import { BlogArticleCard } from './parts'

const PAGE_SIZE = 12

export default function BlogList() {
  // useSWRInfinite handles "load more" page accumulation natively —
  // no manual offset/append state (avoids stale-closure & duplicate appends).
  const { data, size, setSize, isLoading, isValidating, error } =
    useSWRInfinite(
      (pageIndex) => ['news-list', pageIndex],
      ([, pageIndex]) =>
        numerologyApi.getNewsList({
          limit: PAGE_SIZE,
          offset: (pageIndex as number) * PAGE_SIZE,
        }),
      { revalidateFirstPage: false, revalidateOnFocus: false }
    )

  const items = useMemo(() => (data ? data.flatMap((p) => p.data) : []), [data])
  const total = data?.[0]?.total ?? 0
  const hasMore = items.length < total
  const isLoadingMore = isValidating && !!data && size > 1

  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: 'calc(100vh - var(--header-height))',
        py: { xs: 5, md: 8 },
        background:
          'radial-gradient(circle at 12% 8%, rgba(249,106,45,0.16) 0%, transparent 45%),' +
          'radial-gradient(circle at 88% 92%, rgba(111,73,253,0.18) 0%, transparent 50%),' +
          'linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)',
        color: '#fff',
      }}
    >
      <Loading isOpen={isLoading && items.length === 0} />
      <Container maxWidth={false}>
        {/* Heading */}
        <Box mb={{ xs: 4, md: 6 }}>
          <IconTwoRhombus />
          <Typography
            component="h1"
            className="text-heading"
            sx={{ textTransform: 'uppercase' }}
          >
            Blog tra cứu thần số học
          </Typography>
          <Typography sx={{ color: 'rgba(255,255,255,0.78)', mt: 1.5, maxWidth: 640 }}>
            Kiến thức, hướng dẫn và góc nhìn chuyên sâu về thần số học Pythagoras
            — cập nhật liên tục để bạn hiểu sâu hơn về các con số của chính mình.
          </Typography>
        </Box>

        {error && items.length === 0 ? (
          <Typography sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Không tải được danh sách bài viết. Vui lòng thử lại sau.
          </Typography>
        ) : (
          <>
            <Grid container spacing={3}>
              {items.map((article) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={article.id}>
                  <BlogArticleCard article={article} />
                </Grid>
              ))}
            </Grid>

            {items.length === 0 && !isLoading && (
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', mt: 2 }}>
                Chưa có bài viết nào.
              </Typography>
            )}

            {hasMore && (
              <Box textAlign="center" mt={5}>
                <Button
                  variant="outlined"
                  size="large"
                  disabled={isLoadingMore}
                  onClick={() => setSize(size + 1)}
                  sx={{
                    color: '#fff',
                    borderColor: 'rgba(255,255,255,0.35)',
                    '&:hover': {
                      borderColor: 'var(--primary, #F96A2D)',
                      bgcolor: 'rgba(249,106,45,0.12)',
                    },
                  }}
                >
                  {isLoadingMore ? 'Đang tải...' : 'Xem thêm bài viết'}
                </Button>
              </Box>
            )}
          </>
        )}
      </Container>
    </Box>
  )
}
