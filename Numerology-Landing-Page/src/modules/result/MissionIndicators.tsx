import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface MissionIndicatorsProps {
  isVip: boolean
}

export default function MissionIndicators({
  isVip = false,
}: MissionIndicatorsProps) {
  return (
    <BoxContentDetail
      title="8. CHỈ SỐ SỨ MỆNH CỦA BẠN LÀ:"
      isIconEyeOff={!isVip}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Box>
          <Typography fontStyle={'italic'}>
            Trong Thần số học, chỉ số sứ mệnh giúp bạn biết cách đạt được mục
            tiêu của bạn, lớn và nhỏ. Sứ mệnh khác với số đường đời. Con số
            đường đời của bạn ám chỉ đến mục đích tổng thể lớn hơn của bạn. Chỉ
            số sứ mệnh của bạn tập trung nhiều hơn vào các đặc điểm, tính cách
            của bạn. Nhưng số đường đời và số mệnh của bạn có thể đi đôi với
            nhau. Theo thần số học, số đường đời của bạn cho bạn biết bạn đến
            cuộc đời này để làm gì, số sứ mệnh của bạn mô tả cách bạn tiếp tục
            thực hiện nó.Phép tính đơn giản của chúng tôi xác định số sứ mệnh
            giúp bạn xác định các đặc điểm chính của mình và nơi bạn xuất sắc
            trong cuộc sống. Không chỉ một giai đoạn của cuộc đời, mà con số này
            tác động vào mọi giai đoạn của cuộc đời bạn.
          </Typography>
          <Typography fontStyle={'italic'}>
            Bạn có thể chọn một con đường đi, nhưng nó có thể không phải lúc nào
            cũng đúng. Chỉ số này giúp xác định con đường nào là con đường phù
            hợp sẽ khiến bạn hài lòng và mãn nguyện.
          </Typography>
        </Box>
        <Box>
          {!isVip && (
            <AlertWarning>
              Bạn cần nâng cấp Vip để xem được luận giải của mục này!
            </AlertWarning>
          )}
        </Box>
      </Box>
    </BoxContentDetail>
  )
}
