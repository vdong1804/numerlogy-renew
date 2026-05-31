import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface LifeCycleProps {
  isVip?: boolean
}

export default function LifeCycle({ isVip = false }: LifeCycleProps) {
  return (
    <BoxContentDetail title="4. CHU KỲ ĐƯỜNG ĐỜI">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Typography fontStyle={'italic'}>
          Cuộc đời mỗi người thường sẽ trải qua ba giai đoạn tuyệt vời trên
          đường đời. Về mặt số học, ba thời kỳ này (Gieo hạt, Chín, Thu hoạch)
          và các đặc điểm chính của chúng được mô tả bằng các con số của chu kỳ
          đường đời.
        </Typography>

        <Typography fontStyle={'italic'}>
          Chu kỳ đầu tiên (chu kỳ gieo hạt) thể hiện giai đoạn đầu của cuộc
          sống. Nó được ví như sự lớn lên của hạt giống, là một giai đoạn mà bạn
          phải mò mẫm để tìm ra bản chất thật của mình; đồng thời, chúng ta đang
          cố gắng đối phó với những tác động mạnh mẽ xuất hiện trong môi trường
          sống của bạn, cha mẹ và các điều kiện kinh tế xã hội, gia đình, bạn
          bè. Tuy nhiên, trong thời thơ ấu, ảnh hưởng của chu kỳ này rất thấp mà
          nó trở nên dễ nhận thấy hơn chủ yếu từ cuối tuổi thiếu niên của bạn
          cho đến hết chu kỳ đầu tiên này.
        </Typography>

        <Typography fontStyle={'italic'}>
          Sự thay đổi từ Chu kỳ đầu tiên sang Chu kỳ thứ hai có thể gây ngạc
          nhiên vì đó là sự thay đổi đầu tiên trong cuộc đời.
        </Typography>
        <Typography fontStyle={'italic'}>
          Chu kỳ thứ hai (chu kỳ chín) có thể được so sánh với quá trình chín
          của trái cây. Chu kỳ này là giai đoạn giữa cuộc đời dẫn đến sự xuất
          hiện chậm chạp của các tài năng sáng tạo cá nhân. Vài năm đầu của chu
          kỳ này thể hiện một cuộc đấu tranh để tìm vị trí của bạn trên thế
          giới, giai đoạn còn lại của chu kỳ cho thấy bạn có mức độ làm chủ bản
          thân và ảnh hưởng lớn hơn đến môi trường xung quanh bạn.
        </Typography>
        <Typography fontStyle={'italic'}>
          Chu kỳ thứ hai sau đó nó bắt đầu mờ dần và ảnh hưởng của Chu kỳ thứ ba
          bắt đầu thể hiện. Trong quá trình chuyển đổi này, bạn có thể mong đợi
          một sự thay đổi lớn trong cuộc đời mình.
        </Typography>
        <Typography fontStyle={'italic'}>
          Chu kỳ thứ ba, hay chu kỳ cuối cùng, có thể được so sánh với vụ thu
          hoạch, đại diện cho sự phát triển nở hoa của con người bên trong chúng
          ta, bản chất thực sự của chúng ta cuối cùng đã thành hiện thực. Trong
          giai đoạn này, bạn có mức độ thể hiện bản thân và quyền lực lớn nhất.
          Kiến thức và kinh nghiệm tích lũy giúp bạn có nhiều khả năng hơn để
          đưa ra quyết định sáng suốt.
        </Typography>
        <Box
          component={'img'}
          src="https://nhansoungdung.com/Contents/upload/webp/khuc-giao-thoi-trong-chu-ky-9-nam-thay-doi.webp"
          sx={{
            width: {
              xs: '100%',
              md: '75%',
            },
            borderRadius: '10px',
            margin: '0 auto',
          }}
        ></Box>
        {!isVip && (
          <AlertWarning>Chỉ tài khoản Vip mới xem được mục này!</AlertWarning>
        )}
      </Box>
    </BoxContentDetail>
  )
}
