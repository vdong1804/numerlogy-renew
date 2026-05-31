import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'

import { Box, Container, Typography } from '@mui/material'
import { Keyboard, Navigation, Pagination } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

import { IconTwoRhombus } from '@/components/icon'

import { BookCard, CourseCard } from './parts'

const COURSE_LIST = [
  {
    id: 1,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    detailCourseUrl: '#',
    imgUrl:
      'https://media.istockphoto.com/id/1291081296/vi/anh/khu%C3%B4n-m%E1%BA%B7t-v%C5%A9-tr%E1%BB%A5-v%C3%A0-s%E1%BB%91-h%E1%BB%8Dc-c%E1%BB%A7a-ph%E1%BB%A5-n%E1%BB%AF.jpg?s=2048x2048&w=is&k=20&c=xr-xMowk82z48i8sf0vbOzcM3DiovF-TxMTNDyxJzo4=',
    description:
      'Những con số xuất hiện trong cuộc sống của bạn không phải là một sự trùng hợp ngẫu nhiên. Với những ai đang trên hành trình thức tỉnh tâm linh, những con số này đều mang một ý nghĩa vô cùng đặc biệt. Hãy cùng thầy Louis Nguyễn giải mã bí ẩn của chúng, cũng như cách những con số này ảnh hưởng đến cuộc chúng ta.',
  },
  {
    id: 2,
    title: '3 bí mật giúp bạn định hướng nghề nghiệp, phát triển sự nghiệp',
    detailCourseUrl: '#',
    imgUrl:
      'https://media.istockphoto.com/id/1289955669/vi/anh/khu%C3%B4n-m%E1%BA%B7t-kh%C3%B4ng-gian-v%C3%A0-s%E1%BB%91-h%E1%BB%8Dc-c%E1%BB%A7a-ng%C6%B0%E1%BB%9Di-ph%E1%BB%A5-n%E1%BB%AF.jpg?s=2048x2048&w=is&k=20&c=w60kMvjQpa8TV1BrDVhY13eaK5ngroLEGrd2qv1tBnk=',
    description:
      'Chương trình do nhà nghiên cứu ứng dụng thần số học, chuyên gia tâm lý học hành vi thầy Louis Nguyễn đặc biệt thiết kế dành riêng cho những ai đang gặp vướng mắc, bế tắc trong công việc, chưa thể khai phá toàn lực bản thân, phát triển tối đa điểm mạnh của mình để đạt được sự nghiệp thành công như mong muốn.',
  },
  {
    id: 3,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    detailCourseUrl: '#',
    imgUrl:
      'https://media.istockphoto.com/id/1291081296/vi/anh/khu%C3%B4n-m%E1%BA%B7t-v%C5%A9-tr%E1%BB%A5-v%C3%A0-s%E1%BB%91-h%E1%BB%8Dc-c%E1%BB%A7a-ph%E1%BB%A5-n%E1%BB%AF.jpg?s=2048x2048&w=is&k=20&c=xr-xMowk82z48i8sf0vbOzcM3DiovF-TxMTNDyxJzo4=',
    description:
      'Những con số xuất hiện trong cuộc sống của bạn không phải là một sự trùng hợp ngẫu nhiên. Với những ai đang trên hành trình thức tỉnh tâm linh, những con số này đều mang một ý nghĩa vô cùng đặc biệt. Hãy cùng thầy Louis Nguyễn giải mã bí ẩn của chúng, cũng như cách những con số này ảnh hưởng đến cuộc chúng ta.',
  },
  {
    id: 4,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    detailCourseUrl: '#',
    imgUrl:
      'https://media.istockphoto.com/id/1291081296/vi/anh/khu%C3%B4n-m%E1%BA%B7t-v%C5%A9-tr%E1%BB%A5-v%C3%A0-s%E1%BB%91-h%E1%BB%8Dc-c%E1%BB%A7a-ph%E1%BB%A5-n%E1%BB%AF.jpg?s=2048x2048&w=is&k=20&c=xr-xMowk82z48i8sf0vbOzcM3DiovF-TxMTNDyxJzo4=',
    description:
      'Những con số xuất hiện trong cuộc sống của bạn không phải là một sự trùng hợp ngẫu nhiên. Với những ai đang trên hành trình thức tỉnh tâm linh, những con số này đều mang một ý nghĩa vô cùng đặc biệt. Hãy cùng thầy Louis Nguyễn giải mã bí ẩn của chúng, cũng như cách những con số này ảnh hưởng đến cuộc chúng ta.',
  },
]
const NUMEROLOGY_BOOK = [
  {
    id: 1,
    name: 'Báo cáo thần số học trọn đời',
    imgUrl: '/assets/images/book_numerology.png',
    isActive: true,
  },
  {
    id: 2,
    name: 'Báo cáo đặt tên khai sinh',
    imgUrl: '/assets/images/bao-cao-dat-ten-khai-sinh.png',
    isActive: false,
  },
  {
    id: 3,
    name: 'Báo cáo định hướng nghề nghiệp',
    imgUrl: '/assets/images/bao-cao-dinh-huong-nghe-nghiep.jpg',
    isActive: false,
  },
  {
    id: 4,
    name: 'Báo cáo đặt tên danh xưng',
    imgUrl: '/assets/images/bao-cao-dat-ten-danh-xung.jpg',
    isActive: false,
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
              Chương trình đào tạo thần số học
            </Typography>
            <Typography className="text-heading">
              Do thầy Aladanh thành trực tiếp đứng lớp
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
        <Box mt={4}>
          <Box>
            <IconTwoRhombus />
            <Typography className="text-heading">
              Ứng dụng Thần số học
            </Typography>
            <Typography className="text-heading">
              Thầy Aladanh Thành nghiên cứu
            </Typography>
          </Box>
          <Box
            mt={2.5}
            display={'grid'}
            gridTemplateColumns="repeat(12, 1fr)"
            gap={2.5}
          >
            {NUMEROLOGY_BOOK.map((bookItem) => (
              <Box
                sx={{
                  gridColumn: {
                    xs: 'span 6',
                    md: 'span 3',
                  },
                }}
                key={bookItem.id}
              >
                <BookCard bookInfo={bookItem} />
              </Box>
            ))}
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
