import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ThinkingIndicatorProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Trong thần số học, chỉ số năng lực tư duy tiết lộ cách trí óc bạn hoạt động
    trong các tình huống khác nhau của cuộc sống. Bằng việc biết cách suy nghĩ
    của bạn, mọi người có thể hiểu được tính cách của bạn. Con số này cũng tiết
    lộ về mức độ thông minh và khả năng tư duy logic của bạn.
  </Typography>
)

export default function ThinkingIndicator({
  isVip = false,
}: ThinkingIndicatorProps) {
  return (
    <BoxContentDetail
      title="23. CHỈ SỐ NĂNG LỰC TƯ DUY CỦA BẠN LÀ:"
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
