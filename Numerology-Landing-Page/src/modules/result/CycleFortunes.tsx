import { Box, Typography } from '@mui/material'
import * as React from 'react'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface ICycleFortunesProps {
  isVip?: boolean
}

export default function CycleFortunes({ isVip = false }: ICycleFortunesProps) {
  return (
    <BoxContentDetail title="1. CHU KỲ VẬN SỐ CỦA BẠN">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 1.25 }}>
        <Typography>
          Biểu đồ này cho biết bạn đang ở đâu trong chu kỳ vận số của mình. Theo
          thần số học, chu kỳ phát triển của đời người sẽ lặp lại mỗi 9 năm. Với
          mỗi năm có số cá nhân là 1, cuộc đời lại bắt đầu một chu kỳ mới với
          xuất phát cao hơn chu kỳ trước. Ảnh hưởng của biểu đồ này sẽ thể hiện
          mạnh nhất trong giai đoạn từ mốc đỉnh cao đầu tiên đến mốc đỉnh cao
          cuối cùng (Xem ở mục{' '}
          <Typography color="primary" fontStyle={'italic'} component={'span'}>
            Kim tự tháp thấn số
          </Typography>
          )
        </Typography>
        <Typography>
          Đoạn biểu đồ đi lên cho thấy giai đoạn cuộc sống sẽ có nhiều cơ hội,
          thay đổi hoặc phát triển từ bên ngoài.
        </Typography>
        <Typography>
          Đoạn biểu đồ đi xuống cho thấy giai đoạn cuộc sống có nhiều thay đổi
          bên trong bản thân, bạn nên dành thời gian phát triển nội tâm, trí tuệ
          của mình hơn là tập trung vào những thứ bên ngoài trong giai đoạn này.
        </Typography>
        <Box textAlign={'center'} my={2}>
          <Box
            component={'img'}
            src="https://i.ytimg.com/vi/7EmtA3WjzfQ/maxresdefault.jpg"
            alt="Chu ki van so"
            sx={{
              width: {
                xs: '100%',
                md: '75%',
                lg: '50%',
              },
              objectFit: 'cover',
              borderRadius: '5px',
            }}
          />
        </Box>
        <Typography fontWeight={700}>
          Theo thần số học vào năm 2023, chỉ số vận niên thế giới là số 7 ảnh
          hưởng tới toàn bộ nhân loại. Bạn mang chỉ số đường đời 9 và 2023 bạn
          mang chỉ số năm (vận niên cá nhân) là 2, một năm trong giai đoạn đầu
          của chu kỳ vận số. Xu hướng và những điều bạn nên chú ý trong năm này
          như sau:
        </Typography>
        {!isVip && (
          <AlertWarning>
            Chỉ tài khoản VIP mới xem được toàn bộ luận giải và hướng dẫn cho
            năm 2023
          </AlertWarning>
        )}
      </Box>
    </BoxContentDetail>
  )
}
