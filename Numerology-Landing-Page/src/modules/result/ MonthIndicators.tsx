import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail, BoxIndicators } from './parts'

export interface MonthIndicatorsProps {
  isVip: boolean
}

export default function MonthIndicators({
  isVip = false,
}: MonthIndicatorsProps) {
  return (
    <BoxContentDetail title="7. CHỈ SỐ CÁC THÁNG">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Box>
          <Typography fontStyle={'italic'}>
            Những con số này cho biết ở mỗi tháng sẽ có những điều gì có khả
            năng xảy ra và bạn nên tập trung làm việc như thế nào, theo con số
            nào nhưng ở mức độ bao quát thấp hơn chỉ số năm
          </Typography>
          <Typography fontStyle={'italic'}>
            Lưu ý: Sau khi sử dụng VIP, mỗi năm bạn vào lại website tra cứu hoặc
            tải lại file để xem luận giải 3 năm tiếp theo và các nội dung luận
            giải mới nếu có!
          </Typography>
        </Box>
        <Box display={'flex'} flexDirection={'column'} rowGap={'5px'}>
          <BoxIndicators title="Tháng 4/2023" />
          <BoxIndicators title="Tháng 4/2023" />
          <BoxIndicators title="Tháng 6/2023" />
        </Box>
        {!isVip && (
          <AlertWarning>
            Mục này cho biết bạn nên làm gì trong những tháng sắp tới để mọi
            việc thuận lợi. Bạn cần nâng cấp Vip để xem được luận giải của mục
            này.
          </AlertWarning>
        )}
      </Box>
    </BoxContentDetail>
  )
}
