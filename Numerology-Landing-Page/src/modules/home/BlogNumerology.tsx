import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'

import { Box, Button, Container } from '@mui/material'
import { useCallback, useRef } from 'react'
import type { Swiper as SwiperType } from 'swiper'
import { Keyboard, Navigation, Pagination } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'
import useSWR from 'swr'

import { ButtonMoveSlice } from '@/components/button'
import { IconNextSlice, IconPrevSlice } from '@/components/icon'
import { Loading } from '@/components/loading'
import numerologyApi from '@/pages/api/numerologyApi'

import { BlogNumerologyCard, TittlePage } from './parts'

export default function BlogNumerology() {
  const sliderRef = useRef<SwiperType>()
  const handlePrev = useCallback(() => {
    if (!sliderRef.current) return
    sliderRef.current?.slidePrev()
  }, [])

  const handleNext = useCallback(() => {
    if (!sliderRef.current) return
    sliderRef.current?.slideNext()
  }, [])

  // API blog list

  const {
    data: newsList,
    isLoading: isLoadingBlog,
    error,
  } = useSWR('news-top', () => numerologyApi.getNewsTop())
  if (error) return null
  return (
    <Box className="blog-numerology-wrapper">
      <Loading isOpen={isLoadingBlog} />
      <Container maxWidth={false}>
        <Box marginLeft={{ lg: '120px' }} position={'relative'}>
          <Swiper
            spaceBetween={20}
            slidesPerView={'auto'}
            // watchOverflow={true}
            breakpoints={{
              360: {
                slidesPerView: 'auto',
              },
              576: {
                slidesPerView: 2,
              },
              768: {
                slidesPerView: 2.5,
              },
              880: {
                slidesPerView: 3,
              },
              1024: {
                slidesPerView: 3.6,
              },
            }}
            className="mySwiper"
            keyboard={{
              enabled: true,
            }}
            pagination={{
              clickable: true,
            }}
            modules={[Keyboard, Pagination, Navigation]}
            onBeforeInit={(swiper) => {
              sliderRef.current = swiper
            }}
          >
            {newsList?.data.map((news) => {
              return (
                <SwiperSlide key={news.id}>
                  <BlogNumerologyCard newsInfo={news} />
                </SwiperSlide>
              )
            })}
          </Swiper>
          <Box
            sx={{
              position: 'absolute',
              left: {
                xs: 0,
                lg: 132,
              },
              top: -100,
            }}
          >
            <TittlePage>Blog tra cứu thần số học </TittlePage>
          </Box>
          <Button
            variant="outlined"
            sx={{ position: 'absolute', top: 'calc(100% + 32px)', right: 0 }}
          >
            Xem tất cả
          </Button>
          <Box
            sx={{
              position: 'absolute',
              top: 'calc(100% + 62px)',
              left: {
                xs: 0,
                lg: 132,
              },
            }}
          >
            <ButtonMoveSlice
              variant="outlined"
              sx={{ transform: 'translate(20%,-80%) rotate(45deg)' }}
              onClick={handlePrev}
            >
              <Box sx={{ transform: 'rotate(-45deg)' }}>
                <IconPrevSlice />
              </Box>
            </ButtonMoveSlice>
            <ButtonMoveSlice
              variant="contained"
              sx={{ transform: 'rotate(45deg)' }}
              onClick={handleNext}
            >
              <Box sx={{ transform: 'rotate(-45deg)' }}>
                <IconNextSlice />
              </Box>
            </ButtonMoveSlice>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
