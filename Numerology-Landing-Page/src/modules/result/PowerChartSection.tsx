import { Box, Grid } from '@mui/material'

import type { NumerologyIndicator, PowerChart } from '@/models'

import NumberCard from './NumberCard'
import LoShuGrid from './parts/LoShuGrid'
import SectionHeading from './parts/SectionHeading'

export interface PowerChartSectionProps {
  powerChart: PowerChart
  missingNumbers: NumerologyIndicator[]
}

/**
 * Biểu đồ năng lượng: two Lo Shu grids (birth + name) followed by the list of
 * missing numbers ("Những Con Số Còn Thiếu").
 */
export default function PowerChartSection({
  powerChart,
  missingNumbers,
}: PowerChartSectionProps) {
  return (
    <Box component="section">
      <SectionHeading
        title="Biểu Đồ Năng Lượng"
        subtitle="Sức mạnh nguyên thủy từ ngày sinh và tên gọi của bạn"
      />

      <Box
        p={2.5}
        bgcolor="#011625"
        borderRadius={2.5}
        sx={{ border: '1px solid rgba(68, 187, 255, 0.12)' }}
      >
        <Grid container spacing={4} justifyContent="center">
          <Grid item xs={12} sm={6} md="auto">
            <LoShuGrid title="Biểu đồ ngày sinh" counts={powerChart.birth} />
          </Grid>
          <Grid item xs={12} sm={6} md="auto">
            <LoShuGrid title="Biểu đồ tên gọi" counts={powerChart.name} />
          </Grid>
        </Grid>
      </Box>

      {missingNumbers?.length > 0 && (
        <Box mt={3.75}>
          <SectionHeading
            title="Những Con Số Còn Thiếu"
            subtitle="Các con số vắng mặt — những bài học bạn cần bồi đắp"
          />
          <Grid container spacing={2.5} mt={0}>
            {missingNumbers.map((item) => (
              <Grid key={item.code} item xs={12} sm={6} md={4} lg={3}>
                <NumberCard label="Số còn thiếu" indicator={item} compact />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  )
}
