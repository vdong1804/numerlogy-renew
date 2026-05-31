import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface OvercomeDifficultiesProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Những người khác nhau phản ứng khác nhau với những thách thức mà họ phải
      đối mặt trong cuộc sống. Một số người có thói quen rút lui khỏi tình huống
      khó khăn để suy nghĩ thấu đáo vấn đề; những người khác rút lui khỏi cảm
      xúc của họ, để thoát khỏi cảm giác khó chịu. Một số người bùng nổ vì cảm
      xúc, nhưng để cơn bùng nổ trôi qua nhanh chóng, còn người khác nán lại với
      cảm xúc của họ, suy nghĩ nhiều về cảm xúc đó trong nội tâm.
    </Typography>
    <Typography fontStyle={'italic'}>
      Chỉ số này sẽ hướng dẫn bạn cách tốt nhất để đối phó với các tình huống
      khó khăn hoặc đe dọa. Bạn cũng biết về cách tốt nhất để sử dụng khả năng
      của mình để đối mặt với những thách thức khác nhau trong cuộc sống và cách
      đối phó với những thời điểm khó khăn.
    </Typography>
  </>
)

export default function OvercomeDifficulties({
  isVip = false,
}: OvercomeDifficultiesProps) {
  return (
    <BoxContentDetail
      title="22. CHỈ SỐ VƯỢT KHÓ CỦA BẠN LÀ:"
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
