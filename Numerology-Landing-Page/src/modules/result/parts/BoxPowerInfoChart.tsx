import { Box, Grid, Typography } from '@mui/material'
import * as React from 'react'

interface BoxPowerInfoChartProps {
  title: string
  description?: string
}
export default function BoxPowerInfoChart({
  title,
  description,
}: BoxPowerInfoChartProps) {
  return (
    <Box textAlign={'center'}>
      <Grid
        container
        width={292}
        className="power-info-chart"
        margin={'0 auto'}
      >
        {Array.from(Array(9).keys()).map((item) => (
          <Grid key={item} item xs={4}>
            <Box
              height={52}
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Typography
                component={'span'}
                color="common.white"
                fontWeight={700}
              >
                {item + 1}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
      <Typography mt={1.25} fontWeight={600}>
        {title}
      </Typography>
      {description && (
        <Typography fontStyle={'italic'} mt={0.5}>
          {description}
        </Typography>
      )}
    </Box>
  )
}
