import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface SoulIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Linh hồn, sự khao khát từ sâu bên trong của mỗi người. Chỉ số này hé lộ linh
    hồn hay sâu thẳm trong bạn mong muốn bạn trở thành con người như thế nào thì
    mới cảm thấy thỏa mãn và trọn vẹn. Nói cách khác, nếu bạn có những đặc điểm
    tích cực của chỉ số này, linh hồn bạn sẽ cảm thấy hạnh phúc.
  </Typography>
)

export default function SoulIndicators({ isVip = false }: SoulIndicatorsProps) {
  return (
    <BoxContentDetail
      title="12. CHỈ SỐ LINH HỒN CỦA BẠN LÀ:"
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
