import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface AttitudeIndicatorProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Số thái độ là một thành phần quan trọng của số học. Nó mô tả cách bạn thể
      hiện mình với phần còn lại của thế giới một cách tự nhiên, đặc biệt là
      trong những lần gặp gỡ đầu tiên.
    </Typography>
    <Typography fontStyle={'italic'}>
      Mặc dù không phải lúc nào bạn cũng có thể nhận thức được hành động của
      mình, nhưng con số thái độ của bạn mô tả cách bạn hành động với người khác
      một cách tự nhiên (có thể hiểu giống như bản năng của bạn).
    </Typography>
    <Typography fontStyle={'italic'}>
      Một khi bạn hiểu về cách bạn cư xử tự nhiên với người khác và trong cuộc
      sống nói chung, bạn có thể thay đổi nó nếu bạn cảm thấy thích.
    </Typography>
  </>
)

export default function AttitudeIndicator({
  isVip = false,
}: AttitudeIndicatorProps) {
  return (
    <BoxContentDetail
      title="20. CHỈ SỐ THÁI ĐỘ CỦA BẠN LÀ:"
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
