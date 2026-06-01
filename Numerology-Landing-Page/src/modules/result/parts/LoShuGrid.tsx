import { Box, Grid, Typography } from '@mui/material'

export interface LoShuGridProps {
  title: string
  /** Digit-frequency map, keys "1".."9". */
  counts: Record<string, number>
}

/**
 * 3x3 Lo Shu-style grid. Each cell shows its digit repeated `count` times
 * (empty when 0). Reuses the existing `power-info-chart` SCSS borders.
 */
export default function LoShuGrid({ title, counts }: LoShuGridProps) {
  return (
    <Box textAlign="center">
      <Grid
        container
        width={292}
        className="power-info-chart"
        margin="0 auto"
      >
        {Array.from({ length: 9 }, (_, i) => i + 1).map((digit) => {
          const count = counts?.[String(digit)] ?? 0
          return (
            <Grid key={digit} item xs={4}>
              <Box
                height={64}
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <Typography
                  component="span"
                  fontWeight={700}
                  letterSpacing={2}
                  sx={{
                    color: '#44BBFF',
                    textShadow: '0px 2px 10px rgba(27, 90, 251, 0.55)',
                  }}
                >
                  {count ? String(digit).repeat(count) : ''}
                </Typography>
              </Box>
            </Grid>
          )
        })}
      </Grid>
      <Typography mt={1.25} fontWeight={600}>
        {title}
      </Typography>
    </Box>
  )
}
