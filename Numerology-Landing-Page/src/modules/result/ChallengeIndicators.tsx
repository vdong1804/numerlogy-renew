import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ChallengeIndicatorsProps {
  isVip: boolean
}

export default function ChallengeIndicators({
  isVip = false,
}: ChallengeIndicatorsProps) {
  return (
    <BoxContentDetail
      title="9. CHỈ SỐ THỬ THÁCH SỨ MỆNH CỦA BẠN LÀ:"
      isIconEyeOff={!isVip}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Box>
          <Typography fontStyle={'italic'}>
            Chỉ số này cho biết những kiểu thử thách thường gặp nhất trong suốt
            cuộc đời mà bạn sẽ phải vượt qua nó. Bạn hãy nhớ theo thần số học,
            một thách thức không phải là một mối đe dọa. Đây là thử thách bắt
            nguồn từ họ tên khai sinh của bạn, nó nói về những lựa chọn mà bạn
            có thể thực hiện sẽ cải thiện hoàn cảnh chung của mình.
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
