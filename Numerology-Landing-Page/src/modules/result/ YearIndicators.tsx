import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail, BoxIndicators } from './parts'

export interface YearIndicatorsProps {
  isVip: boolean
}

export default function YearIndicators({ isVip = false }: YearIndicatorsProps) {
  return (
    <BoxContentDetail title="6. CÁC CHỈ SỐ NĂM">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Box>
          <Typography fontStyle={'italic'}>
            Những con số này cho biết ở mỗi năm bạn nên tập trung định hướng
            phát triển theo con số nào. Thường thì cuộc đời sẽ tự đẩy bạn đi
            theo những con số này. Nếu đi lệch ra bạn thường sẽ bị cảm thấy cuộc
            sống mất cân bằng hoặc bất an. Còn nếu đi đúng hướng bạn thường cảm
            thấy rất bình an và thuận lợi.
          </Typography>
          <Typography fontStyle={'italic'}>
            Lưu ý: Sau khi sử dụng VIP, mỗi năm bạn vào lại website tra cứu hoặc
            tải lại file để xem luận giải 3 năm tiếp theo và các nội dung luận
            giải mới nếu có!
          </Typography>
        </Box>
        <Box display={'flex'} flexDirection={'column'} rowGap={'5px'}>
          <BoxIndicators title="Năm 2023" />
          <BoxIndicators title="Năm 2024" />
          <BoxIndicators title="Năm 2025" />
        </Box>
        {!isVip && (
          <AlertWarning>
            Mục này cho biết bạn nên đi theo hướng nào trong những năm sắp tới
            để đạt thành công. Bạn cần nâng cấp Vip để xem được luận giải chi
            tiết của mục này.
          </AlertWarning>
        )}
      </Box>
    </BoxContentDetail>
  )
}
