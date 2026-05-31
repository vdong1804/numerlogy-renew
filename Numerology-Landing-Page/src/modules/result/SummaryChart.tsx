import { Box, Grid } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail, BoxPowerInfoChart } from './parts'

export interface SummaryChartProps {
  isVip: boolean
}

export default function SummaryChart({ isVip = false }: SummaryChartProps) {
  return (
    <BoxContentDetail title="19. BIỂU ĐỒ TÊN VÀ BIỂU ĐỒ TỔNG HỢP">
      <Box
        sx={{ mt: 2.5, display: 'flex', flexDirection: 'column', rowGap: 2.5 }}
      >
        <Grid container spacing={6}>
          <Grid item xs={12} md={6}>
            <Box margin={'0 auto'}>
              <BoxPowerInfoChart
                title="Trung"
                description="Biểu đồ này cho biết những sức mạnh do tên của bạn mang lại. Chủ yếu dùng tên đó để gộp với ngày sinh tạo ra biểu đồ tổng hợp bên cạnh."
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box margin={'0 auto'}>
              <BoxPowerInfoChart
                title="Biểu đồ tổng hợp"
                description="Biểu đồ này thể hiện bù trừ của tên vào ngày sinh của bạn. Các con số của tên (màu đỏ) lấp đầy các khoảng trống trong biểu đồ ngày sinh là đẹp nhất."
              />
            </Box>
          </Grid>
        </Grid>
        <Box>
          {!isVip && (
            <AlertWarning>
              Mục này giải thích chi tiết về sự bù trừ của tên vào ngày sinh của
              bạn. Bạn cần nâng cấp Vip để xem được luận giải của mục này.
            </AlertWarning>
          )}
        </Box>
      </Box>
    </BoxContentDetail>
  )
}
