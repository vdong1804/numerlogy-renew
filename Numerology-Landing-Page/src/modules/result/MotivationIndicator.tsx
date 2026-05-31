import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface MotivationIndicatorProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này thể hiện động lực của bạn để quyết định làm điều mới (người, sự
    vật, sự việc mới).
  </Typography>
)

export default function MotivationIndicator({
  isVip = false,
}: MotivationIndicatorProps) {
  return (
    <BoxContentDetail
      title="24. CHỈ SỐ ĐỘNG LỰC TIẾP CẬN CỦA BẠN LÀ:"
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
