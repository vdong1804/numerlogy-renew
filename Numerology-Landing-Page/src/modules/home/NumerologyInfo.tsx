import { Box, Container, Grid } from '@mui/material'
import * as React from 'react'

import { AccordionCustom } from '@/components/accordion'
import { NumberMeaningExplorer } from '@/modules/numerology-meaning'

import { TittlePage } from './parts'

const NUMEROLOGY_SHARED_LIST = [
  {
    id: 1,
    title: 'Khám phá bản thân theo nhân số học!',
    description:
      'Nhân số học (Thần số học Pythagoras) giải mã con người bạn thông qua ngày tháng năm sinh và họ tên khai sinh. Từ những con số tưởng chừng ngẫu nhiên ấy, bạn sẽ hiểu rõ tính cách, điểm mạnh, điểm yếu, đam mê tiềm ẩn và con đường phát triển phù hợp nhất với mình – để sống đúng với con người thật và phát huy trọn vẹn tiềm năng vốn có.',
  },
  {
    id: 2,
    title: 'Tracuuthansohoc có thể giúp gì cho bạn?',
    description:
      'Chỉ với họ tên và ngày sinh, hệ thống tính toán đầy đủ các chỉ số quan trọng: Số chủ đạo, Số sứ mệnh, Số linh hồn, biểu đồ ngày sinh, các chu kỳ và đỉnh cao cuộc đời. Bạn nhận về bản luận giải chi tiết giúp định hướng sự nghiệp, cải thiện các mối quan hệ, chọn thời điểm hành động phù hợp và đưa ra quyết định sáng suốt hơn trong cuộc sống.',
  },
]
const NUMEROLOGY_INTERESTING = [
  {
    id: 1,
    title: 'Con số chủ đạo (Chỉ đường đời)',
    description:
      'Số chủ đạo (Life Path) được tính từ tổng các chữ số trong ngày tháng năm sinh, là chỉ số quan trọng nhất trong thần số học. Nó cho biết bài học, sứ mệnh và con đường cốt lõi mà bạn được sinh ra để đi qua – từ Số 1 thủ lĩnh độc lập đến Số 9 nhân ái, cùng các Số bậc thầy 11, 22, 33.',
  },
  {
    id: 2,
    title: 'Biểu đồ ngày sinh',
    description:
      'Biểu đồ ngày sinh sắp xếp các chữ số trong ngày sinh của bạn vào lưới 9 ô (theo trục Pythagoras). Số lượng và vị trí các con số tiết lộ những mũi tên sức mạnh, các đặc điểm nổi trội cũng như những khía cạnh còn khuyết thiếu cần được bồi đắp trong tư duy, cảm xúc và hành động.',
  },
  {
    id: 3,
    title: 'Năm cá nhân',
    description:
      'Năm cá nhân là chu kỳ năng lượng vận hành theo vòng lặp từ 1 đến 9, được tính từ ngày, tháng sinh kết hợp với năm hiện tại. Biết mình đang ở năm cá nhân nào giúp bạn nắm bắt được nên khởi đầu, xây dựng, bứt phá hay buông bỏ – để hành động thuận theo dòng chảy thay vì đi ngược lại nó.',
  },
  {
    id: 4,
    title: '4 đỉnh cao đời người trong thần số học Pitago',
    description:
      '4 đỉnh cao (Pinnacles) chia cuộc đời thành bốn giai đoạn lớn, mỗi giai đoạn mang một con số và một loại năng lượng riêng. Chúng cho biết cơ hội, thử thách và bài học trọng tâm của từng chặng đường, giúp bạn chuẩn bị tâm thế và tận dụng đúng thời điểm để vươn tới thành công.',
  },
  {
    id: 5,
    title: 'Các chỉ số trong thần số học và ý nghĩa của chúng',
    description:
      'Bên cạnh Số chủ đạo, bản đồ thần số học của bạn còn gồm nhiều chỉ số: Số sứ mệnh (tài năng và mục tiêu sống), Số linh hồn (khát khao sâu thẳm), Số nhân cách (hình ảnh bên ngoài), Số thái độ, Số trưởng thành… Khi kết hợp tất cả, bạn có được bức tranh toàn diện và chính xác về con người mình.',
  },
  {
    id: 6,
    title: 'Công cụ bói tình yêu theo thần số học',
    description:
      'Bằng cách so sánh Số chủ đạo và các chỉ số cốt lõi của hai người, thần số học chỉ ra mức độ hòa hợp, những điểm tương đồng tự nhiên cũng như khác biệt cần dung hòa trong một mối quan hệ. Đây là công cụ thú vị giúp bạn thấu hiểu đối phương và xây dựng tình yêu, tình bạn bền vững hơn.',
  },
]
export default function NumerologyInfo() {
  return (
    <Box className="numerology-info-wrapper">
      <Container maxWidth={false}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            rowGap: 5,
            pt: 5,
            pb: 8,
          }}
        >
          <Box>
            <TittlePage>Ý nghĩa các con số trong thần số học</TittlePage>
            <Box mt={2.5}>
              <NumberMeaningExplorer />
            </Box>
          </Box>

          <Box>
            <TittlePage>Đôi lời chia sẻ về thần số học</TittlePage>
            <Box mt={2.5}>
              <Grid container columnSpacing={2.5} rowSpacing={2.5}>
                {NUMEROLOGY_SHARED_LIST.map(({ id, title, description }) => (
                  <Grid key={id} item xs={12} md={6}>
                    <AccordionCustom title={title} description={description} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Box>

          <Box>
            <TittlePage>
              Kiến thức thú vị trong thần số học pythagoras không nên bỏ nỡ
            </TittlePage>
            <Box mt={2.5}>
              <Grid container columnSpacing={2.5} rowSpacing={2.5}>
                {NUMEROLOGY_INTERESTING.map(({ id, title, description }) => (
                  <Grid key={id} item xs={12} md={6}>
                    <AccordionCustom title={title} description={description} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
