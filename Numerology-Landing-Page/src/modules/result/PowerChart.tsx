import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail, BoxPowerInfoChart } from './parts'

export interface PowerChartProps {
  isVip: boolean
}

export default function PowerChart({ isVip = false }: PowerChartProps) {
  return (
    <BoxContentDetail title="18. BIỂU ĐỒ SỨC MẠNH CỦA BẠN (rất quan trọng)">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Box>
          <Typography fontStyle={'italic'}>
            Biểu đồ này còn được gọi là biểu đồ ngày sinh do được tạo ra từ ngày
            sinh, biểu đồ này thể hiện sức mạnh nguyên thủy của bạn. Nó cho thấy
            tổng quan các ưu nhược điểm về năng lực, sức mạnh của bạn (thể chất,
            tinh thần, trí tuệ) và cho biết rất nhiều các điểm mạnh điểm yếu của
            bạn.
          </Typography>
          <Typography fontStyle={'italic'}>
            Tóm lại biểu đồ này giống như đề bài toán mà vũ trụ gửi cho bạn, bạn
            cần hiểu đề để giải được bài toán thì cuộc sống của bạn sẽ cân bằng
            và tốt đẹp hơn nhiều.
          </Typography>
          <Typography fontStyle={'italic'}>
            Lưu ý rằng tên thường dùng của bạn có thể bù trừ vào những điểm yếu
            của biểu đồ này, vì vậy hãy tìm hiểu thêm biểu đồ tổng hợp để đặt
            một tên mới cho bạn nếu cần thiết. Tên mới này có thể dùng ở
            facebook, zalo,...
          </Typography>
        </Box>
        <Box margin={'0 auto'}>
          <BoxPowerInfoChart title="Biểu đồ sức mạnh (Biểu đồ ngày sinh) của bạn" />
        </Box>
        <Box>
          {!isVip && (
            <AlertWarning>
              Mục này giải thích chi tiết về biểu đồ sức mạnh và giải pháp của
              chúng tôi cho bạn. Bạn cần nâng cấp Vip để xem được luận giải của
              mục này.
            </AlertWarning>
          )}
        </Box>
      </Box>
    </BoxContentDetail>
  )
}
