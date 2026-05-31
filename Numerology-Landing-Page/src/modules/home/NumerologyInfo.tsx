import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import { Box, Button, Container, Grid, Typography } from '@mui/material'
import * as React from 'react'

import { AccordionCustom } from '@/components/accordion'

import { TittlePage } from './parts'

const NUMEROLOGY_SHARED_LIST = [
  {
    id: 1,
    title: 'Khám phá bản thân theo nhân số học!',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 2,
    title: 'Tracuuthansohoc có thể giúp gì cho bạn?',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget. Lorem ipsum dolor sit amet, consectetur adipiscing elit',
  },
]
const NUMEROLOGY_INTERESTING = [
  {
    id: 1,
    title: 'Con số chủ đạo (Chỉ đường đời)',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 2,
    title: 'Biểu đồ ngày sinh',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 3,
    title: 'Năm cá nhân',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 4,
    title: '4 đỉnh cao đời người trong thần số học Pitago',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 5,
    title: 'Các chỉ số trong thần số học và ý nghĩa của chúng',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
  },
  {
    id: 6,
    title: 'Công cụ bói tình yêu theo thần số học',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse malesuada lacus ex, sit amet blandit leo lobortis eget.',
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
              <Grid container bgcolor={'#081D2D'}>
                <Grid item xs={6} lg={8}>
                  <Grid
                    container
                    borderTop={'2px solid #0E263B'}
                    borderLeft={'2px solid #0E263B'}
                  >
                    {Array.from(Array(12).keys()).map((item) => (
                      <Grid
                        key={item}
                        item
                        xs={6}
                        md={4}
                        lg={3}
                        borderBottom={'2px solid #0E263B'}
                        borderRight={'2px solid #0E263B'}
                      >
                        <Box
                          py={'14px'}
                          // px={5}
                          height={'120px'}
                          textAlign={'center'}
                        >
                          <Typography
                            sx={{
                              fontFamily: 'var(--philosopher-font)',
                              fontSize: 26,
                              lineHeight: '29px',
                            }}
                          >
                            Số
                          </Typography>
                          <Typography
                            component={'span'}
                            color="primary"
                            sx={{
                              fontFamily: 'var(--philosopher-font)',
                              fontSize: 70,
                              lineHeight: '78px',
                              fontWeight: 700,
                            }}
                          >
                            {item + 1}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
                <Grid
                  item
                  xs={6}
                  lg={4}
                  sx={{
                    border: '2px solid #0E263B',
                    borderLeft: 0,
                    height: 'inherit',
                  }}
                >
                  <Box
                    py={'14px'}
                    sx={{
                      px: {
                        xs: 2,
                        md: 5,
                      },
                    }}
                    height={'100%'}
                  >
                    <Box>
                      <Typography
                        sx={{
                          fontFamily: 'var(--philosopher-font)',
                          fontSize: 26,
                          lineHeight: 0,
                        }}
                      >
                        Số
                        <Typography
                          component={'span'}
                          color="primary"
                          sx={{
                            fontFamily: 'var(--philosopher-font)',
                            fontSize: 70,
                            fontWeight: 700,
                            marginLeft: 1.5,
                            lineHeight: '50px',
                          }}
                        >
                          1
                        </Typography>
                      </Typography>
                    </Box>
                    <Typography mt={2.5}>
                      Thần số học số 1 là hiện thân của sự táo bạo, đổi mới,
                      chấp nhận rủi ro, khả năng phục hồi và đi theo trái tim
                      mình. Nhân số học số 1 giúp phát triển sự sáng tạo và sự
                      tự tin của bạn trong mọi khía cạnh của cuộc sống. Mục đích
                      sống của những người có số chủ đạo 1 là mang tới năng
                      lượng sáng tạo tích cực, đạt được sự độc lập trong các mối
                      quan hệ của bản thân.
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      sx={{ mt: 4 }}
                      endIcon={<ChevronRightIcon fontSize="large" />}
                    >
                      Xem chi tiết
                    </Button>
                  </Box>
                </Grid>
              </Grid>
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
