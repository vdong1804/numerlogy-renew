/**
 * Interactive "Ý nghĩa các con số" explorer.
 *
 * Left: grid of selectable core numbers (1–9, 11, 22, 33).
 * Right: meaning panel that updates when a number is clicked.
 * "Xem chi tiết" links to the dedicated /y-nghia-con-so/[so] page.
 */
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import { Box, Button, Grid, Typography } from '@mui/material'
import { useRouter } from 'next/router'
import { useState } from 'react'

import { NUMBER_MEANINGS } from './numerology-meaning-data'

export default function NumberMeaningExplorer() {
  const router = useRouter()
  const [activeIndex, setActiveIndex] = useState(0)
  const active = NUMBER_MEANINGS[activeIndex] ?? NUMBER_MEANINGS[0]!

  return (
    <Grid container bgcolor={'#081D2D'}>
      {/* Left: number grid */}
      <Grid item xs={6} lg={8}>
        <Grid
          container
          borderTop={'2px solid #0E263B'}
          borderLeft={'2px solid #0E263B'}
        >
          {NUMBER_MEANINGS.map((meaning, index) => {
            const isActive = index === activeIndex
            return (
              <Grid
                key={meaning.number}
                item
                xs={6}
                md={4}
                lg={3}
                borderBottom={'2px solid #0E263B'}
                borderRight={'2px solid #0E263B'}
              >
                <Box
                  component={'button'}
                  type={'button'}
                  onClick={() => setActiveIndex(index)}
                  aria-pressed={isActive}
                  aria-label={`Xem ý nghĩa số ${meaning.number}`}
                  sx={{
                    appearance: 'none',
                    border: 0,
                    cursor: 'pointer',
                    width: '100%',
                    py: '14px',
                    height: '120px',
                    textAlign: 'center',
                    color: 'inherit',
                    background: isActive
                      ? 'linear-gradient(180deg, rgba(249,106,45,0.18) 0%, rgba(249,106,45,0.04) 100%)'
                      : 'transparent',
                    boxShadow: isActive
                      ? 'inset 0 0 0 2px var(--primary, #F96A2D)'
                      : 'none',
                    transition: 'background 0.2s ease, box-shadow 0.2s ease',
                    '&:hover': {
                      background: 'rgba(249,106,45,0.08)',
                    },
                  }}
                >
                  <Typography
                    sx={{
                      fontFamily: 'var(--philosopher-font)',
                      fontSize: 26,
                      lineHeight: '29px',
                    }}
                  >
                    Số
                  </Typography>
                  <Typography
                    component={'span'}
                    color={isActive ? 'primary' : 'inherit'}
                    sx={{
                      fontFamily: 'var(--philosopher-font)',
                      fontSize: 70,
                      lineHeight: '78px',
                      fontWeight: 700,
                    }}
                  >
                    {meaning.number}
                  </Typography>
                </Box>
              </Grid>
            )
          })}
        </Grid>
      </Grid>

      {/* Right: active number meaning */}
      <Grid
        item
        xs={6}
        lg={4}
        sx={{
          border: '2px solid #0E263B',
          borderLeft: 0,
          height: 'inherit',
        }}
      >
        <Box
          py={'14px'}
          sx={{
            px: {
              xs: 2,
              md: 5,
            },
          }}
          height={'100%'}
          display={'flex'}
          flexDirection={'column'}
        >
          <Box>
            <Typography
              sx={{
                fontFamily: 'var(--philosopher-font)',
                fontSize: 26,
                lineHeight: 0,
              }}
            >
              Số
              <Typography
                component={'span'}
                color="primary"
                sx={{
                  fontFamily: 'var(--philosopher-font)',
                  fontSize: 70,
                  fontWeight: 700,
                  marginLeft: 1.5,
                  lineHeight: '50px',
                }}
              >
                {active.number}
              </Typography>
            </Typography>
          </Box>
          <Typography
            color="primary"
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontSize: 22,
              fontWeight: 700,
              mt: 2,
            }}
          >
            {active.title}
          </Typography>
          <Typography sx={{ fontSize: 13, opacity: 0.8, mt: 0.5 }}>
            {active.keyword}
          </Typography>
          <Typography mt={2}>{active.summary}</Typography>
          <Button
            onClick={() => router.push(`/y-nghia-con-so/${active.slug}`)}
            variant="contained"
            color="primary"
            sx={{ mt: 'auto', alignSelf: 'flex-start', pt: 1 }}
            endIcon={<ChevronRightIcon fontSize="large" />}
          >
            Xem chi tiết
          </Button>
        </Box>
      </Grid>
    </Grid>
  )
}
