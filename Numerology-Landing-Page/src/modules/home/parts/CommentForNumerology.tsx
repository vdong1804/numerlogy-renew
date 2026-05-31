import { Box, Typography } from '@mui/material'
import { Navigation, Pagination } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

import BoxComment from './BoxComment'
import TittlePage from './TitlePage'

const commentExamples = [
  {
    id: 1,
    user: {
      id: 1,
      name: 'Mai Linh',
      job: 'MC - Design',
      avatar:
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80',
    },
    content:
      'Trước đây tôi thường xuyên có những mối quan hệ không tốt và đem đến những ảnh hưởng tiêu cực. Khi có quá nhiều mối hệ như vậy khiến tôi băn khoăn suy nghĩ có phải vấn đề đến từ chính bản thân mình hay không?”. Suy nghĩ này khiến cho tôi từ một người đầy tự tin trở nên rụt rè, chỉ biết thu mình lại ở những nơi đông người. Nhưng từ khi biết đến Nhân số học, tôi nhận ra vấn đề không phải do cá nhân chưa đủ tốt, lí do là bởi tôi không biết cách chọn lọc. Bằng cách tra cứu Thần số học Pythagoras, tôi hiểu thêm về chính mình và bản thân phù hợp với những người như thế nào.',
  },
  {
    id: 2,
    user: {
      id: 2,
      name: 'Ngọc Bích',
      job: 'MC - Design',
      avatar:
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=387&q=80',
    },
    content:
      'Một người từng ở tuổi 30 vẫn phải chuyển hết công việc này đến việc khác, tôi ước mình biết đến Thần số học Pythagoras sớm hơn. Ở giai đoạn lựa chọn nghề nghiệp vì không hiểu được hết ưu nhược điểm, thế mạnh của bản thân nên tôi đã “học đại” một ngành hot lúc bấy giờ. Nhưng kết quả thì sao? Những tháng ngày sau đó của tôi trượt dài trong sự chán chường vì thiếu đi sự đam mê: đi học điểm số luôn ở hạng cuối, lúc đi làm thì 8 tiếng ở văn phòng kéo dài như cả tuần… Nhưng tôi không đủ tự tin để làm lại vì bản thân không biết mình thật sự thích và giỏi ở lĩnh vực nào. ',
  },
]
export default function CommentForNumerology() {
  return (
    <Box
      className="reader-comment-wrapper"
      height={'940px'}
      position={'relative'}
    >
      <TittlePage>Góc chia sẻ</TittlePage>
      <Typography
        sx={{
          fontSize: 18,
          marginTop: 2,
          maxWidth: '560px',
        }}
      >
        Chia sẻ từ những cá nhân đã tìm thấy sự đột phá cuộc đời nhờ Nhân số học
      </Typography>
      <Box
        pt={4}
        px={2.5}
        paddingBottom={4}
        sx={{
          position: 'absolute',
          left: 0,
          top: '50%',
          width: {
            md: '735px',
            xs: '100%',
          },
          transform: 'translateY(-50%)',
          borderRadius: '5px',
        }}
        bgcolor={'#012233'}
      >
        <Swiper
          spaceBetween={20}
          slidesPerView={'auto'}
          watchOverflow={true}
          breakpoints={{
            360: {
              slidesPerView: 1,
            },
            650: {
              slidesPerView: 2,
            },
          }}
          className="mySwiper"
          pagination={{
            clickable: true,
          }}
          navigation={true}
          modules={[Pagination, Navigation]}
        >
          {commentExamples.map(({ id, user, content }) => {
            return (
              <SwiperSlide key={id}>
                <BoxComment user={user} content={content} />
              </SwiperSlide>
            )
          })}
        </Swiper>
      </Box>
    </Box>
  )
}
