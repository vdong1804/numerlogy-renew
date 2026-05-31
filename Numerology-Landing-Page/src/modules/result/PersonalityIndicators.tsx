import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface PersonalityIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Bạn biết bạn là ai. Bạn biết tâm trí của bạn, suy nghĩ của bạn, ý kiến của
      bạn và có một cảm giác về tính cách của bạn. Tuy nhiên, những người khác
      không nhìn bạn như cách bạn nhìn thấy chính mình.
    </Typography>
    <Typography fontStyle={'italic'}>
      Chỉ số này sẽ giúp bạn nhìn thấy những gì mình gửi ra thế giới. Bạn sẽ
      hiểu tại sao một số người rời bỏ bạn, một số ở lại với bạn và một số không
      bao giờ cố gắng. Nó cực kỳ quan trọng về mặt số học vì nó sẽ cho biết
      những gì bạn gửi ra bên ngoài và từ đó người khác đánh giá và nhìn nhận
      bạn như thế nào.
    </Typography>
  </>
)

export default function PersonalityIndicators({
  isVip = false,
}: PersonalityIndicatorsProps) {
  return (
    <BoxContentDetail
      title="14. CHỈ SỐ NHÂN CÁCH CỦA BẠN LÀ:"
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
