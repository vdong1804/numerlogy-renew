import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface MatureCapacityIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này cho bạn biết cần phải làm gì để có thể nhanh chóng đưa các bài
    học mà cuộc đời đã dạy bạn vào việc hoàn thành sứ mệnh của cuộc đời. Hay nói
    cách khác, nó là sự kết nối giữa đường đời của bạn và sứ mệnh của bạn. Nếu
    chỉ số này trùng với năng lực tự nhiên của bạn thì thật là tuyệt vời!
  </Typography>
)

export default function MatureCapacityIndicators({
  isVip = false,
}: MatureCapacityIndicatorsProps) {
  return (
    <BoxContentDetail
      title="11. CHỈ SỐ NĂNG LỰC TRƯỞNG THÀNH CỦA BẠN LÀ:"
      isIconEyeOff={!isVip}
      intro={<Intro />}
    >
      <Box>
        {!isVip && (
          <AlertWarning>
            Bạn cần nâng cấp Vip để xem được luận giải của mục này!
          </AlertWarning>
        )}
      </Box>
    </BoxContentDetail>
  )
}
