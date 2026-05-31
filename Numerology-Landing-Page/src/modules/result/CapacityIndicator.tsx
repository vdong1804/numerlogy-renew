import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface CapacityIndicatorProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này thể hiện khả năng tiếp cận, thiên thướng hành động của bạn khi
    gặp điều mới (người, sự vật, sự việc mới).
  </Typography>
)

export default function CapacityIndicator({
  isVip = false,
}: CapacityIndicatorProps) {
  return (
    <BoxContentDetail
      title="25. CHỈ SỐ NĂNG LỰC TIẾP CẬN CỦA BẠN LÀ:"
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
