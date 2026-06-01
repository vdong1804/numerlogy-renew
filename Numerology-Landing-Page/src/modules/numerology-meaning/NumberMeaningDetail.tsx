/**
 * Detail view for a single core number meaning.
 * Rendered by /y-nghia-con-so/[so]. Mirrors the home page's
 * dark cosmic design language (uses PageShell-style framing here directly).
 */
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import { Box, Button, Chip, Container, Grid, Typography } from '@mui/material'
import Image from 'next/image'
import { useRouter } from 'next/router'

import type { NumberMeaning } from './numerology-meaning-data'
import { NUMBER_MEANINGS } from './numerology-meaning-data'

export interface NumberMeaningDetailProps {
  meaning: NumberMeaning
}

export default function NumberMeaningDetail({
  meaning,
}: NumberMeaningDetailProps) {
  const router = useRouter()
  const others = NUMBER_MEANINGS.filter((m) => m.slug !== meaning.slug)

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
        overflow: 'hidden',
      }}
    >
      <Container maxWidth={'lg'}>
        {/* Breadcrumb / back */}
        <Button
          onClick={() => router.push('/#tra-cuu')}
          startIcon={<ArrowBackIcon />}
          sx={{ color: 'rgba(255,255,255,0.8)', mb: 3 }}
        >
          Về trang chủ
        </Button>

        {/* Hero */}
        <Grid container spacing={4} alignItems={'center'} mb={{ xs: 4, md: 6 }}>
          <Grid item xs={12} md={4} textAlign={'center'}>
            <Box
              sx={{
                position: 'relative',
                width: { xs: 160, md: 220 },
                height: { xs: 160, md: 220 },
                mx: 'auto',
              }}
            >
              <Image
                src={meaning.image}
                alt={`Số ${meaning.number} – ${meaning.title}`}
                fill
                sizes="220px"
                style={{ objectFit: 'contain' }}
                priority
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={8}>
            <Typography
              sx={{
                fontFamily: 'var(--philosopher-font)',
                fontSize: { xs: 20, md: 26 },
                opacity: 0.85,
              }}
            >
              Thần số học · Số chủ đạo
            </Typography>
            <Typography
              component={'h1'}
              sx={{
                fontFamily: 'var(--philosopher-font)',
                fontWeight: 700,
                fontSize: { xs: '2.25rem', md: '3.25rem' },
                lineHeight: 1.1,
              }}
            >
              Số {meaning.number} – {meaning.title}
            </Typography>
            <Chip
              label={meaning.keyword}
              sx={{
                mt: 1.5,
                color: '#fff',
                bgcolor: 'rgba(249,106,45,0.18)',
                border: '1px solid rgba(249,106,45,0.5)',
                fontWeight: 600,
                height: 'auto',
                py: 0.75,
                '& .MuiChip-label': { whiteSpace: 'normal' },
              }}
            />
            <Typography mt={2.5} sx={{ color: 'rgba(255,255,255,0.85)' }}>
              {meaning.summary}
            </Typography>
          </Grid>
        </Grid>

        {/* Detail sections */}
        <Grid container spacing={2.5}>
          {meaning.sections.map((section) => (
            <Grid item xs={12} md={6} key={section.heading}>
              <Box
                sx={{
                  height: '100%',
                  borderRadius: 3,
                  p: { xs: 2.5, md: 3.5 },
                  bgcolor: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.10)',
                  backdropFilter: 'blur(10px)',
                }}
              >
                <Typography
                  component={'h2'}
                  color="primary"
                  sx={{
                    fontFamily: 'var(--philosopher-font)',
                    fontWeight: 700,
                    fontSize: '1.375rem',
                    mb: 1,
                  }}
                >
                  {section.heading}
                </Typography>
                <Typography sx={{ color: 'rgba(255,255,255,0.85)', lineHeight: 1.7 }}>
                  {section.body}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        {/* Explore other numbers */}
        <Box mt={{ xs: 5, md: 7 }}>
          <Typography
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontWeight: 700,
              fontSize: '1.5rem',
              mb: 2,
            }}
          >
            Khám phá các con số khác
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1.5,
            }}
          >
            {others.map((m) => (
              <Button
                key={m.slug}
                onClick={() => router.push(`/y-nghia-con-so/${m.slug}`)}
                variant="outlined"
                sx={{
                  minWidth: 56,
                  color: '#fff',
                  borderColor: 'rgba(255,255,255,0.25)',
                  fontFamily: 'var(--philosopher-font)',
                  fontSize: 20,
                  fontWeight: 700,
                  '&:hover': {
                    borderColor: 'var(--primary, #F96A2D)',
                    bgcolor: 'rgba(249,106,45,0.12)',
                  },
                }}
              >
                {m.number}
              </Button>
            ))}
          </Box>
        </Box>

        {/* CTA */}
        <Box mt={{ xs: 5, md: 7 }} textAlign={'center'}>
          <Button
            onClick={() => router.push('/#tra-cuu')}
            variant="contained"
            color="primary"
            size="large"
            endIcon={<ChevronRightIcon />}
          >
            Tra cứu thần số học của bạn
          </Button>
        </Box>
      </Container>
    </Box>
  )
}
