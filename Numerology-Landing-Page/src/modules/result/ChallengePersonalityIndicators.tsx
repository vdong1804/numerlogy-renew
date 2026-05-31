import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ChallengePersonalityIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Thái độ và suy nghĩ của bất kỳ một ai về bản thân đều ảnh hưởng tới sức
      khỏe, sự thịnh vượng, mối quan hệ, đời sống tinh thần, ... của người đó.
    </Typography>
    <Typography fontStyle={'italic'}>
      Chỉ số về nhân cách thể hiện phản hồi mà bên ngoài (người khác) cảm thấy
      chúng ta về các lựa chọn, suy nghĩ, lời nói và việc làm của chúng ta. Khi
      bạn không hài lòng với hoàn cảnh của mình, chính chỉ số này sẽ thể hiện
      phản ứng với hoàn cảnh đó - nó có thể tạo ra một kế hoạch hành động phù
      hợp theo khía cạnh tích cực, hoặc tạo ra suy nghĩ tiêu cực như giận dữ, tự
      phê bình, phòng thủ hoặc chống đối.
    </Typography>
    <Typography fontStyle={'italic'}>
      Những suy nghĩ và cảm xúc tiêu cực này có thể phá hoại kế hoạch của bạn.
      Nếu không có kế hoạch nào được thực hiện, chúng sẽ thu hút những hoàn cảnh
      khó khăn hơn, điều này có thể dẫn đến những xáo trộn về thể chất và tinh
      thần. Và chỉ số thử thách nhân cách sẽ cho bạn biết những gì bạn làm để
      đối diện với những tình huống như vậy.
    </Typography>
  </>
)

export default function ChallengePersonalityIndicators({
  isVip = false,
}: ChallengePersonalityIndicatorsProps) {
  return (
    <BoxContentDetail
      title="15. CHỈ SỐ THỬ THÁCH NHÂN CÁCH CỦA BẠN LÀ:"
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
