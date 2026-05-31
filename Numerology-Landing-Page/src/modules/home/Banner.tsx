import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import { Box, Button, Container, Grid, Typography } from '@mui/material'
import { animated, useSpring } from '@react-spring/web'
import Image from 'next/image'
import React from 'react'

import { IconCheck } from '@/components/icon'
import { formatNumberDE } from '@/utils/helpers'

export default function Banner() {
  const viewAnimated = useSpring({
    num: 1123256,
    from: { num: 0 },
  })
  const totalMemberAnimate = useSpring({
    num: 23256,
    from: { num: 0 },
  })
  const publicationReportAnimate = useSpring({
    num: 23256,
    from: { num: 0 },
  })
  const opacityAnimate = useSpring({
    from: {
      opacity: 0,
      x: 500,
    },
    to: {
      opacity: 1,
      x: 0,
    },
  })
  const AnimatedTypography = animated(Typography)
  return (
    <Box
      className="banner-wrapper"
      sx={{
        position: 'relative',
        py: {
          xs: 6,
          lg: 12,
        },
        overflow: 'hidden',
      }}
      minHeight={'calc(100vh - var(--header-height))'}
    >
      <Container maxWidth={false}>
        <Grid
          container
          columnSpacing={2}
          rowGap={4}
          alignItems={'center'}
          justifyContent={'center'}
        >
          <Grid item xs={12} md={7} lg={6}>
            <Box display={'flex'} flexDirection={'column'} rowGap={'20px'}>
              <Typography sx={{ fontWeight: 500, fontSize: '1.375rem' }}>
                Tra Cứu Thần Số Học Cùng Thầy
              </Typography>
              <Typography
                sx={{
                  marginTop: '-10px',
                }}
                className="name-teacher-heading"
              >
                Aladanh Thành
              </Typography>
              <Box display={'flex'} flexDirection={'column'} rowGap={1}>
                <Box display={'flex'} columnGap={1.5} alignItems={'center'}>
                  <IconCheck />
                  <Typography fontSize={14}>
                    Nhà sáng lập hệ thống thần số học được ứng dụng phổ biến tại
                    Việt Nam
                  </Typography>
                </Box>
                <Box display={'flex'} columnGap={1.5} alignItems={'center'}>
                  <IconCheck />
                  <Typography fontSize={14}>
                    Luận giải chi tiết – chính xác – tin cậy
                  </Typography>
                </Box>
              </Box>
              <Box
                display={'flex'}
                sx={{
                  columnGap: {
                    lg: 5,
                    xs: 2,
                  },
                }}
              >
                <Box display={'flex'} flexDirection={'column'} width={1 / 3}>
                  <AnimatedTypography
                    // component={'span'}
                    sx={{
                      fontFamily: 'var(--philosopher-font)',
                      fontSize: '2rem',
                    }}
                    color="primary"
                  >
                    {totalMemberAnimate.num.to(
                      (val) => `${formatNumberDE(val)} +`
                    )}
                  </AnimatedTypography>
                  <Typography
                    component={'span'}
                    sx={{
                      fontSize: '1.375rem',
                    }}
                  >
                    Học viên qua các khóa học
                  </Typography>
                </Box>

                <Box display={'flex'} flexDirection={'column'} width={1 / 3}>
                  <AnimatedTypography
                    // component={'span'}
                    sx={{
                      fontFamily: 'var(--philosopher-font)',
                      fontSize: '2rem',
                    }}
                    color="primary"
                  >
                    {viewAnimated.num.to((val) => formatNumberDE(val))}
                  </AnimatedTypography>
                  <Typography
                    component={'span'}
                    sx={{
                      fontSize: '1.375rem',
                    }}
                  >
                    Lượt tra cứu
                  </Typography>
                </Box>
                <Box display={'flex'} flexDirection={'column'} width={1 / 3}>
                  <AnimatedTypography
                    // component={'span'}
                    sx={{
                      fontFamily: 'var(--philosopher-font)',
                      fontSize: '2rem',
                    }}
                    color="primary"
                  >
                    {publicationReportAnimate.num.to(
                      (val) => `${formatNumberDE(val)} +`
                    )}
                  </AnimatedTypography>
                  <Typography
                    component={'span'}
                    sx={{
                      fontSize: '1.375rem',
                    }}
                  >
                    Báo cáo xuất bản
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="contained"
                color="primary"
                size="large"
                sx={{ width: 'fit-content' }}
                endIcon={<ArrowForwardIcon fontSize="large" />}
                component="a"
                href="#tra-cuu"
              >
                Tra cứu các chỉ số của bạn ngay
              </Button>
              <Typography fontSize={14} textAlign={'justify'}>
                Những nghiên cứu về Thần số học của Thầy Aladanh Thành đang mang
                đến một làn sóng tích cực trong đại chúng Việt Nam. Không chỉ là
                các phân tích để giúp mỗi người tìm ra những tiềm năng thực sự
                và trả lời được câu hỏi mình là ai trong cuộc đời này, những
                nghiên cứu sâu và rộng khắp các lĩnh vực của thầy còn giúp hàng
                triệu người lựa chọn được con đường đi đúng đắn, giúp cho những
                người làm kinh doanh tìm ra định hướng phù hợp trong chiến lược
                và trong quản trị doanh nghiệp, quan hệ khách hàng.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={5} lg={6}>
            <Box
              sx={{
                textAlign: 'center',
                maxWidth: {
                  xs: '550px',
                  lg: '100%',
                },
                margin: '0 auto',
                mr: {
                  lg: -8,
                },
                ml: {
                  lg: 10,
                },
              }}
            >
              {/* Wrap with animated.div to preserve fade-in; next/image handles optimized loading */}
              <animated.div style={opacityAnimate}>
                <Image
                  src="/assets/images/adalash_banner.png"
                  alt="Thầy Aladanh Thành – giảng viên thần số học"
                  width={600}
                  height={700}
                  style={{ width: '100%', height: 'auto' }}
                  priority
                />
              </animated.div>
            </Box>
          </Grid>
        </Grid>
      </Container>

      <Box
        sx={{
          position: 'absolute',
          right: 0,
          top: '100%',
          zIndex: 1,
          transform: 'translateY(-50%)',
          opacity: {
            xs: 0.6,
            lg: 1,
          },
        }}
      >
        <img src="/assets/images/zodiac.png" alt="Vòng hoàng đạo thần số học" />
      </Box>
    </Box>
  )
}
