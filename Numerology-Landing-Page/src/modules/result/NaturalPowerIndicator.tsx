import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface NaturalPowerIndicatorProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này cho bạn biết năng khiếu bẩm sinh, thứ mà bạn có thể làm dễ dàng,
    cũng như những tài năng và năng lực cụ thể sẽ hỗ trợ bạn trên đường đời.
  </Typography>
)

export default function NaturalPowerIndicator({
  isVip = false,
}: NaturalPowerIndicatorProps) {
  return (
    <BoxContentDetail
      title="21. CHỈ SỐ NĂNG LỰC TỰ NHIÊN CỦA BẠN LÀ:"
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
