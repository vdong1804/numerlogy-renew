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
      job: 'Số chủ đạo 2 · Nhân viên truyền thông',
      avatar: '/assets/images/avatar-circle.png',
    },
    content:
      'Tôi mang số chủ đạo 2 – một người sống thiên về cảm xúc và luôn đặt mối quan hệ lên hàng đầu. Trước đây tôi hay tự trách mình mỗi khi một mối quan hệ đổ vỡ, dần dần trở nên rụt rè và thu mình. Khi tra cứu Thần số học Pythagoras, tôi mới hiểu sự nhạy cảm ấy chính là điểm mạnh của số 2, vấn đề chỉ là tôi chưa biết cách đặt ranh giới và chọn lọc người phù hợp. Giờ tôi tự tin hơn rất nhiều và biết trân trọng giá trị của bản thân.',
  },
  {
    id: 2,
    user: {
      id: 2,
      name: 'Ngọc Bích',
      job: 'Số chủ đạo 5 · Chuyên viên kinh doanh',
      avatar: '/assets/images/avatar-circle.png',
    },
    content:
      'Ngoài 30 tuổi mà tôi vẫn nhảy việc liên tục, lúc nào cũng thấy bí bách. Ước gì tôi biết đến Thần số học sớm hơn. Hóa ra tôi mang số chủ đạo 5 – con người của tự do, trải nghiệm và sự đa dạng, nên những công việc lặp đi lặp lại khiến tôi ngột ngạt là điều dễ hiểu. Khi hiểu được thế mạnh thật sự của mình, tôi chuyển hẳn sang lĩnh vực kinh doanh – nơi tôi được di chuyển, gặp gỡ và thử thách mỗi ngày. Lần đầu tiên tôi thấy mình đi đúng đường.',
  },
  {
    id: 3,
    user: {
      id: 3,
      name: 'Quốc Anh',
      job: 'Số chủ đạo 8 · Quản lý dự án',
      avatar: '/assets/images/avatar-circle.png',
    },
    content:
      'Là số chủ đạo 8, tôi luôn khao khát thành công và địa vị, nhưng cũng vì thế mà lao vào công việc đến mức kiệt sức và bỏ bê gia đình. Bản luận giải thần số học chỉ ra rằng bài học lớn nhất của số 8 là cân bằng giữa vật chất và tinh thần. Tôi học cách dùng năng lực tổ chức của mình một cách khôn ngoan hơn, biết dừng lại đúng lúc. Sự nghiệp vẫn đi lên, mà tôi lại tìm lại được sự bình yên bên những người mình thương.',
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
