import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ChallengeSoulIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Linh hồn mong muốn được trải nghiệm và trưởng thành, mọi nguyên liệu cho
      sự trưởng thành đó không bao giờ hoàn hảo, và sự trưởng thành không bao
      giờ xảy ra nếu không có đấu tranh.
    </Typography>
    <Typography fontStyle={'italic'}>
      Chỉ số thử thách linh hồn này đại diện cho những trở ngại mà linh hồn mang
      theo khi nhập thể để bạn bắt đầu kiếp sống này, vượt qua chúng là một
      nhiệm vụ quan trọng trong suốt cuộc đời. Hiểu về chỉ số linh hồn và thử
      thách của nó có thể nói lên nhiều điều về mục đích hoặc sứ mệnh của bạn
      trong cuộc sống.
    </Typography>
  </>
)

export default function ChallengeSoulIndicators({
  isVip = false,
}: ChallengeSoulIndicatorsProps) {
  return (
    <BoxContentDetail
      title="13. CHỈ SỐ THỬ THÁCH LINH HỒN CỦA BẠN LÀ:"
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
