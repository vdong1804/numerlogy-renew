import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface WeaknessIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Các chỉ số này thể hiện những điểm yếu của bạn mà kiếp trước bạn chưa khắc
    phục được hoặc có thể ngay ở kiếp này còn tồn đọng. Nên sự hoàn thành của
    cuộc đời bạn là khắc phục được các số còn thiếu này.
  </Typography>
)

export default function WeaknessIndicators({
  isVip = false,
}: WeaknessIndicatorsProps) {
  return (
    <BoxContentDetail
      title="16. CÁC CHỈ SỐ ĐIỂM YẾU CỦA BẠN LÀ:"
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
