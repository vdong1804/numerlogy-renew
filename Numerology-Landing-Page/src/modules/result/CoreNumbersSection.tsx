import { Box, Grid } from '@mui/material'

import type { CoreNumbers } from '@/models'

import NumberCard from './NumberCard'
import SectionHeading from './parts/SectionHeading'

export interface CoreNumbersSectionProps {
  core: CoreNumbers
}

/** Ordered map of core-number keys → Vietnamese labels. */
const CORE_LABELS: Array<{ key: keyof CoreNumbers; label: string }> = [
  { key: 'su_menh', label: 'Số Sứ Mệnh' },
  { key: 'linh_hon', label: 'Số Linh Hồn' },
  { key: 'nhan_cach', label: 'Số Nhân Cách' },
  { key: 'thai_do', label: 'Số Thái Độ' },
  { key: 'truong_thanh', label: 'Số Trưởng Thành' },
  { key: 'ngay_sinh', label: 'Số Ngày Sinh' },
  { key: 'noi_cam', label: 'Số Nội Cảm' },
]

/** Responsive grid of the 7 core numbers. */
export default function CoreNumbersSection({ core }: CoreNumbersSectionProps) {
  return (
    <Box component="section">
      <SectionHeading
        title="Các Chỉ Số Cốt Lõi"
        subtitle="7 con số nền tảng định hình con người bạn"
      />
      <Grid container spacing={2.5} mt={0}>
        {CORE_LABELS.map(({ key, label }) => (
          <Grid key={key} item xs={12} sm={6} md={4}>
            <NumberCard label={label} indicator={core[key]} compact />
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
