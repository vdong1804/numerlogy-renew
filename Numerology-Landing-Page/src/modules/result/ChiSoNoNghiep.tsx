import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ChiSoNoNghiepProps {
  isVip: boolean
}

const Intro = () => (
  <Typography fontStyle={'italic'}>
    Chỉ số này thể hiện các bài học cụ thể mà bạn cần chinh phục trong kiếp này
    vì đã không được học chúng ở kiếp trước. Mỗi chỉ số nợ nghiệp lại có bài học
    và gánh nặng riêng. Tất cả các nghiệp này đều có số 1 đứng đầu tức là đều do
    cái tôi mà ra. Nếu bạn học được cách bỏ đi cái tôi của mình và đức nhẫn nhịn
    sẽ khắc phục được rất nhiều các nhược điểm và nợ nghiệp cho kiếp sau bạn
    nhé!
  </Typography>
)

export default function ChiSoNoNghiep({ isVip = false }: ChiSoNoNghiepProps) {
  return (
    <BoxContentDetail
      title="17. CÁC CHỈ SỐ NỢ NGHIỆP CỦA BẠN LÀ:"
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
