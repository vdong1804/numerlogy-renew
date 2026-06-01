import { Box, Grid } from '@mui/material'

import type { LifePeak } from '@/models'

import NumberCard from './NumberCard'
import SectionHeading from './parts/SectionHeading'

export interface LifePeaksSectionProps {
  peaks: LifePeak[]
  isVip?: boolean
}

/** The 4 life peaks rendered as a timeline of cards (labelled by stage + age). */
export default function LifePeaksSection({
  peaks,
  isVip = false,
}: LifePeaksSectionProps) {
  if (!peaks?.length) return null
  return (
    <Box component="section">
      <SectionHeading
        title="Đỉnh Cao Cuộc Đời"
        subtitle="Bốn giai đoạn đỉnh cao đánh dấu các bước ngoặt lớn"
      />
      <Grid container spacing={2.5} mt={0}>
        {peaks.map((peak) => (
          <Grid key={peak.stage} item xs={12} sm={6} lg={3}>
            <NumberCard
              label={`Đỉnh cao ${peak.stage} — từ ${peak.age_start} tuổi`}
              indicator={peak}
              isVip={isVip}
              compact
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
