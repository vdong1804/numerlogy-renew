import { Box, Grid } from '@mui/material'

import type { NumerologyIndicator } from '@/models'

import NumberCard from './NumberCard'
import SectionHeading from './parts/SectionHeading'

export interface KarmicDebtSectionProps {
  /** Số Nợ Nghiệp indicators (13/14/16/19); empty → section hidden. */
  karmicDebt?: NumerologyIndicator[]
}

/** Số Nợ Nghiệp — only rendered when the person actually carries karmic debt. */
export default function KarmicDebtSection({
  karmicDebt,
}: KarmicDebtSectionProps) {
  if (!karmicDebt || karmicDebt.length === 0) return null
  return (
    <Box component="section">
      <SectionHeading
        title="Số Nợ Nghiệp"
        subtitle="Những bài học nghiệp quả cần hóa giải trong đời này"
      />
      <Grid container spacing={2.5} mt={0}>
        {karmicDebt.map((item) => (
          <Grid item xs={12} md={6} key={String(item.code)}>
            <NumberCard label={`Nợ Nghiệp ${item.code}`} indicator={item} />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
