import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ApproachAttitudeProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này thể hiện cách mà mọi người thường đánh giá về phản ứng của bạn
    với một điều mới (người, sự vật, sự việc mới).
  </Typography>
)

export default function ApproachAttitude({
  isVip = false,
}: ApproachAttitudeProps) {
  return (
    <BoxContentDetail
      title="26. CHỈ SỐ THÁI ĐỘ TIẾP CẬN CỦA BẠN LÀ:"
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
