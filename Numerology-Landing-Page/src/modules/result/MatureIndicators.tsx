import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface MatureIndicatorsProps {
  isVip: boolean
}

const Intro = () => (
  <>
    <Typography fontStyle={'italic'}>
      Số trưởng thành của bạn cho biết hướng thành công và mong muốn tiềm ẩn dần
      dần xuất hiện vào khoảng tuổi từ 40 trở lên (một số người sớm hơn hoặc
      muộn hơn). Mục tiêu cơ bản này bắt đầu xuất hiện khi bạn hiểu rõ hơn về
      bản thân.
    </Typography>
    <Typography fontStyle={'italic'}>
      Với sự hiểu biết về bản thân, bạn sẽ nhận thức rõ hơn về con người của
      mình, mục tiêu thực sự của bạn trong cuộc sống là gì và bạn muốn đặt ra
      hướng đi nào cho cuộc đời mình. Tóm lại, đây là món quà của sự trưởng
      thành: Bạn không còn lãng phí thời gian và năng lượng cho những thứ không
      thuộc bản sắc đặc biệt của riêng bạn.
    </Typography>
    <Typography fontStyle={'italic'}>
      Cho dù hiện tại bạn đang ở độ tuổi nào, cuộc sống của bạn đang được chuyển
      sang một hướng cụ thể, hướng tới một mục tiêu rất cụ thể. Mục tiêu đó có
      thể được xem như một phần thưởng hoặc sự hoàn thành một lời hứa tiềm ẩn
      trong những nỗ lực hiện tại của bạn, mà bạn thường không biết điều đó một
      cách có ý thức. Trong khi các đặc điểm của con số này thường được nhìn
      thấy trong thời thơ ấu, chúng ta có xu hướng mất dần các khía cạnh này cho
      đến khi lớn lên. Nhưng dù sao thì cuộc sống của chúng ta cũng luôn bị ảnh
      hưởng bởi nó.
    </Typography>
    <Typography fontStyle={'italic'}>
      Số trưởng thành của bạn bắt đầu có tác động sâu sắc hơn đến cuộc sống của
      bạn sau 35 tuổi - khoảng thời gian bạn bước vào chu kỳ Đỉnh cao thứ hai
      của mình. Ảnh hưởng của số này tăng đều đặn khi bạn dần cao tuổi hơn.
    </Typography>
  </>
)

export default function MatureIndicators({
  isVip = false,
}: MatureIndicatorsProps) {
  return (
    <BoxContentDetail
      title="10. CHỈ SỐ TRƯỞNG THÀNH CỦA BẠN LÀ:"
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
