import { Box, Grid } from '@mui/material'

import type { PersonalCycle } from '@/models'

import NumberCard from './NumberCard'
import SectionHeading from './parts/SectionHeading'

export interface PersonalCycleSectionProps {
  personal: PersonalCycle
  isVip?: boolean
}

/** Năm / tháng cá nhân — the current personal-cycle numbers. */
export default function PersonalCycleSection({
  personal,
  isVip = false,
}: PersonalCycleSectionProps) {
  if (!personal) return null
  return (
    <Box component="section">
      <SectionHeading
        title="Chu Kỳ Cá Nhân"
        subtitle="Năng lượng đang chi phối bạn trong tháng hiện tại"
      />
      <Grid container spacing={2.5} mt={0}>
        <Grid item xs={12} md={6}>
          <NumberCard
            label="Số Tháng Cá Nhân"
            indicator={personal.thang_ca_nhan}
            isVip={isVip}
          />
        </Grid>
      </Grid>
    </Box>
  )
}
