import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'

import { Box, Container, Typography } from '@mui/material'
import { Keyboard, Navigation, Pagination } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

import { IconTwoRhombus } from '@/components/icon'

import { CourseCard } from './parts'

const COURSE_LIST = [
  {
    id: 1,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    detailCourseUrl: '#',
    imgUrl: '/assets/images/posts/y_nghia_nhung_con_so.png',
    description:
      'Những con số xuất hiện trong cuộc đời bạn không hề là sự trùng hợp ngẫu nhiên. Trong khóa học này, thầy Aladanh Thành giải mã ý nghĩa của từng con số chủ đạo (1–9 và các số bậc thầy 11, 22, 33), giúp bạn hiểu rõ tính cách, tiềm năng và cách ứng dụng năng lượng các con số vào công việc, tình cảm và cuộc sống thường ngày.',
  },
  {
    id: 2,
    title: '3 bí mật giúp bạn định hướng nghề nghiệp, phát triển sự nghiệp',
    detailCourseUrl: '#',
    imgUrl: '/assets/images/posts/cach-tinh-than-so-hoc.jpg',
    description:
      'Chương trình do nhà nghiên cứu ứng dụng thần số học, thầy Aladanh Thành thiết kế dành riêng cho những ai đang bế tắc trong công việc. Dựa trên Số sứ mệnh và biểu đồ ngày sinh, bạn sẽ khám phá thế mạnh bẩm sinh của mình và tìm ra hướng đi sự nghiệp phù hợp nhất để phát triển tối đa tiềm năng.',
  },
  {
    id: 3,
    title: 'Biểu đồ ngày sinh & 4 đỉnh cao cuộc đời trong thần số học Pitago',
    detailCourseUrl: '#',
    imgUrl: '/assets/images/posts/cach_tinh_so_chu_dao.png',
    description:
      'Học cách lập và đọc biểu đồ ngày sinh để nhận diện những mũi tên sức mạnh cùng các khía cạnh còn khuyết thiếu của bản thân. Thầy Aladanh Thành hướng dẫn bạn phân tích 4 đỉnh cao đời người, từ đó nắm bắt được cơ hội và thử thách của từng giai đoạn để chủ động kiến tạo tương lai.',
  },
  {
    id: 4,
    title: 'Chu kỳ Năm – Tháng – Ngày cá nhân và nghệ thuật chọn thời điểm',
    detailCourseUrl: '#',
    imgUrl: '/assets/images/posts/tuoi_doi_than_so_hoc.png',
    description:
      'Mỗi người đều vận hành theo các chu kỳ năng lượng riêng. Khóa học giúp bạn tính Năm, Tháng, Ngày cá nhân để biết khi nào nên khởi đầu, xây dựng, bứt phá hay nghỉ ngơi. Cùng thầy Aladanh Thành học cách thuận theo dòng chảy của các con số để đưa ra quyết định đúng thời điểm.',
  },
]
export default function TrainAndApplication() {
  return (
    <Box py={6} className="train-application-wrapper">
      <Container maxWidth={false}>
        <Box>
          <Box>
            <IconTwoRhombus />
            <Typography className="text-heading">
              BLOG TRA CỨU THẦN SỐ HỌC
            </Typography>
          </Box>
          <Box mt={4}>
            <Swiper
              slidesPerView={3}
              spaceBetween={20}
              pagination={{
                clickable: true,
              }}
              keyboard={{
                enabled: true,
              }}
              // navigation={true}
              modules={[Keyboard, Pagination, Navigation]}
              breakpoints={{
                360: {
                  slidesPerView: 'auto',
                },
                576: {
                  slidesPerView: 2,
                },
                1024: {
                  slidesPerView: 3,
                },
              }}
              className="mySwiper"
            >
              {COURSE_LIST.map((courseItem) => {
                return (
                  <SwiperSlide key={courseItem.id}>
                    <CourseCard courseInfo={courseItem} />
                  </SwiperSlide>
                )
              })}
            </Swiper>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
