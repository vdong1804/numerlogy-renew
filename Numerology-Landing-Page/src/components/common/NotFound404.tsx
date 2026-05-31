/**
 * 404 not-found view — themed to match the home cosmic look.
 */
import { Box, Button, Container, Typography } from '@mui/material'
import { useRouter } from 'next/router'

export default function NotFound404() {
  const router = useRouter()
  return (
    <Box
      sx={{
        minHeight: 'calc(100vh - var(--header-height))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background:
          'radial-gradient(circle at 18% 12%, rgba(249,106,45,0.18) 0%, transparent 45%),' +
          'radial-gradient(circle at 82% 88%, rgba(111,73,253,0.18) 0%, transparent 50%),' +
          'linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)',
        color: '#fff',
        py: { xs: 6, md: 10 },
        px: 2,
      }}
    >
      <Container maxWidth="sm" sx={{ textAlign: 'center' }}>
        <Typography
          component="div"
          sx={{
            fontFamily: 'var(--philosopher-font)',
            fontWeight: 700,
            fontSize: { xs: '6rem', md: '9rem' },
            lineHeight: 1,
            background:
              'linear-gradient(135deg, #F96A2D 0%, #FF8F5E 50%, #6F49FD 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 1,
          }}
        >
          404
        </Typography>
        <Typography
          component="h2"
          sx={{
            fontFamily: 'var(--philosopher-font)',
            fontWeight: 700,
            fontSize: { xs: '1.5rem', md: '2rem' },
            color: '#fff',
            mb: 1.5,
          }}
        >
          Oops! Trang không tồn tại
        </Typography>
        <Typography
          sx={{
            color: 'rgba(255,255,255,0.75)',
            mb: 4,
            fontSize: '1rem',
          }}
        >
          Có vẻ những con số đã dẫn lối bạn đi nhầm đường. Hãy quay về để tiếp tục
          khám phá nhé.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => router.push('/')}
          >
            Về Trang Chủ
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => {
              if (typeof window !== 'undefined' && window.history.length > 1) {
                router.back()
              } else {
                router.push('/')
              }
            }}
            sx={{
              color: '#fff',
              borderColor: 'rgba(255,255,255,0.35)',
              '&:hover': {
                borderColor: '#fff',
                bgcolor: 'rgba(255,255,255,0.08)',
              },
            }}
          >
            Quay Lại
          </Button>
        </Box>
      </Container>
    </Box>
  )
}
