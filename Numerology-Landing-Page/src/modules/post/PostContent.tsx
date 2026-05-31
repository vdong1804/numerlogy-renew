import { Box, Container, Divider, Grid, Typography } from '@mui/material'
import { useCallback, useEffect, useRef } from 'react'

import { RullingNumberForm, SearchNumerologyForm } from '@/components/form'
import { IconTwoRhombus } from '@/components/icon'

import { ContentDescriptionItem, PostCard } from './parts'

const relatedPosts = [
  {
    id: 1,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    imgLink:
      'https://media.istockphoto.com/id/1245857277/vi/anh/n%E1%BB%81n-kh%C3%A1i-ni%E1%BB%87m-s%E1%BB%91-xo%C3%A1y.jpg?s=2048x2048&w=is&k=20&c=ioDCv-DQcXsQnISvz_OpiwSgwmHpjmkGLTaENNuwhYE=',
    to: '#',
  },
  {
    id: 2,
    title: '3 bí mật giúp bạn định hướng nghề nghiệp, phát triển sự nghiệp',
    imgLink:
      'https://media.istockphoto.com/id/1245857277/vi/anh/n%E1%BB%81n-kh%C3%A1i-ni%E1%BB%87m-s%E1%BB%91-xo%C3%A1y.jpg?s=2048x2048&w=is&k=20&c=ioDCv-DQcXsQnISvz_OpiwSgwmHpjmkGLTaENNuwhYE=',
    to: '#',
  },
  {
    id: 3,
    title: '3 bí mật giúp bạn định hướng nghề nghiệp, phát triển sự nghiệp',
    imgLink:
      'https://media.istockphoto.com/id/1245857277/vi/anh/n%E1%BB%81n-kh%C3%A1i-ni%E1%BB%87m-s%E1%BB%91-xo%C3%A1y.jpg?s=2048x2048&w=is&k=20&c=ioDCv-DQcXsQnISvz_OpiwSgwmHpjmkGLTaENNuwhYE=',
    to: '#',
  },
  {
    id: 4,
    title: 'Ý nghĩa các con số thần số học & Ứng dụng vào đời sống',
    imgLink:
      'https://media.istockphoto.com/id/1245857277/vi/anh/n%E1%BB%81n-kh%C3%A1i-ni%E1%BB%87m-s%E1%BB%91-xo%C3%A1y.jpg?s=2048x2048&w=is&k=20&c=ioDCv-DQcXsQnISvz_OpiwSgwmHpjmkGLTaENNuwhYE=',
    to: '#',
  },
]
export default function PostContent() {
  const postRelatedRef = useRef<HTMLDivElement | null>(null)
  const onScroll = useCallback(() => {
    const { pageYOffset } = window
    if (pageYOffset > 1200) {
      if (postRelatedRef && postRelatedRef.current) {
        postRelatedRef.current.style.position = 'sticky'
        postRelatedRef.current.style.top = '110px'
      }
    }
  }, [])

  useEffect(() => {
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
    }
  }, [])
  return (
    <Box component={'section'} py={5}>
      <Container maxWidth={false}>
        <Box display={'flex'} gap={5}>
          {/* Box Left */}
          <Box component={'article'} flex={1}>
            <Box className="intro">
              <Box>
                <Box
                  component={'img'}
                  src="/assets/images/posts/cach-tinh-than-so-hoc.jpg"
                  alt="Cách tính thần số học"
                  sx={{ width: '100%' }}
                />
              </Box>
              <Typography variant="body1" mt={3.75}>
                Trong bộ môn Thần Số Học được phát triển bởi nhà toán học
                Pythagoras, mỗi người trong thế giới này đều được liên kết với
                những con số. Và những con số đó được tính toán dựa trên ngày
                sinh và họ tên của mỗi người. Tuy nhiên,{' '}
                <Typography
                  component={'span'}
                  fontStyle={'italic'}
                  fontWeight={600}
                >
                  cách tính Thần số học
                </Typography>{' '}
                này như thế nào cho đúng là điều mà rất ít người biết. Vậy làm
                thế nào để tính được các con số của bản thân theo Thần số học
                đúng và chuẩn nhất? Hãy cùng Tracuuthansohoc.com đi tìm hiểu về
                cách tính thần số học theo chuẩn Pythagoras nhé!
              </Typography>
              <Box textAlign={'center'} mt={3}>
                <Box width={'fit-content'} margin={'0 auto'}>
                  <Box
                    component={'img'}
                    src="/assets/images/posts/tuoi_doi_than_so_hoc.png"
                    alt="Thần số học là một môn khoa học đã có tuổi đời hơn 2500 năm"
                    sx={{ objectFit: 'cover' }}
                    width={'100%'}
                  />
                  <Typography fontStyle={'italic'} fontWeight={500} mt={0.5}>
                    Thần số học là một môn khoa học đã có tuổi đời hơn 2500 năm
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Box
              className="content"
              sx={{
                mt: 4.5,
                display: 'flex',
                flexDirection: 'column',
                rowGap: 4.5,
              }}
            >
              <ContentDescriptionItem title="Cách tính Thần số học chuẩn Pythagoras theo tên và ngày sinh chuẩn nhất">
                <Typography>
                  Mỗi người trên thế giới này, đều được đại diện bởi một con số
                  bất kỳ. Và với bộ môn Thần số học, khi ta hiểu được ý nghĩa và
                  cách tính các con số, chúng ta sẽ nắm giữ chìa khóa mở ra cánh
                  cửa tổng quan về cuộc sống của mình. Càng tìm hiểu về các con
                  số trong Thần số học, bạn sẽ càng thấy quyền năng của các con
                  số trong thế giới xung quanh bản thân.
                </Typography>
              </ContentDescriptionItem>

              <ContentDescriptionItem title="Cơ sở của cách tính Thần số học cho các chỉ số cá nhân">
                <Typography>
                  Thần số học là một phần nhỏ trong hệ thống các con số bao gồm
                  nghiên cứu tính chất các phép toán, cơ sở phép tính,…Nhưng với
                  Thần số học các con số còn mang một tầng ý nghĩa về sự rung
                  động, về các tần số trong cuộc sống có ảnh hưởng trực tiếp tới
                  con người. Khi nghiên cứu về hành vi, cảm xúc của con người,
                  Thần số học đã cung cấp một lượng thông tin cực kỳ chuẩn xác.
                  Đây chính là cơ sở, tiền đề xây dựng cách tính Thần số học,
                  giúp mọi người có thể tự tính được con số của chính mình và
                  hiểu được ý nghĩa của nó.
                </Typography>
                <Typography>
                  Có 2 cách tính theo tên và ngày sinh, trước tiên chúng ta hãy
                  cùng tìm hiểu về cách tính thần số học theo ngày sinh.
                </Typography>
              </ContentDescriptionItem>

              <ContentDescriptionItem title="Cách tính Thần số học ngày tháng năm sinh thành chữ số đơn">
                <Typography>
                  Mỗi con số trong Thần số học có một định nghĩa riêng biệt. Dù
                  con số ấy xuất hiện ở vị trí nào trong bản đồ, định nghĩa của
                  nó cũng không thay đổi. Tracuuthansohoc hy vọng khi đọc xong
                  bài viết này, bạn có thể ghi nhớ đặc trưng của từng con số và
                  cách diễn giải ra các con số.
                </Typography>
                <Typography>
                  Làm sao mà nhớ nổi ý nghĩa của mọi con số trong vũ trụ? Bạn
                  không phải làm thế. Vì trong Thần số học, mọi con số – từ
                  tuổi, ngày sinh của bạn cho đến ngay cả con số nào dài nhất
                  bạn có thể nghĩ tới – đều có thể dễ dàng rút gọn thành một chữ
                  số đơn. Vì vậy, duy nhất những chữ số đơn sau đây chúng ta cần
                  nhớ: 1, 2, 3, 4, 5, 6, 7, 8, 9. (Có hai con số khác cũng có ý
                  nghĩa là 11 và 22, nhưng chúng ta sẽ tìm hiểu về chúng sau).
                </Typography>
                <Box textAlign={'center'} my={2.5}>
                  <Box width={'fit-content'} margin={'0 auto'}>
                    <Box
                      component={'img'}
                      src="/assets/images/posts/y_nghia_nhung_con_so.png"
                      alt="Thần số học là một môn khoa học đã có tuổi đời hơn 2500 năm"
                      sx={{ objectFit: 'cover' }}
                      width={'100%'}
                    />
                    <Typography fontStyle={'italic'} fontWeight={500} mt={0.5}>
                      Từng số đơn trong nhân số học đều mang 1 ý nghĩa
                    </Typography>
                  </Box>
                </Box>
                <Typography>
                  Rút gọn một số thành một chữ số đơn là việc cực kì dễ dàng –
                  chỉ việc cộng tất cả các chữ số tạo nên con số đó. (Nếu bạn
                  thấy chưa dễ dàng khi tìm hiểu cách tính Thần số học thì mời
                  bạn sử dụng công cụ tính của chúng tôi ở cuối bài viết) Sau
                  đây là ví dụ đối với số 19:
                </Typography>
                <Typography>
                  1. Cộng các chữ số của số này: 1 + 9 = 10
                </Typography>
                <Typography>
                  2. Kết quả ở đây nhiều hơn một chữ số đơn, vì vậy lại lặp lại
                  bước trên bằng cách cộng hai con số và ra kết quả: 1 + 0 = 1
                </Typography>
                <Typography>
                  Trong Thần số học, số 19 được rút gọn thành 1.
                </Typography>
              </ContentDescriptionItem>

              <ContentDescriptionItem title="Cách tính Thần số học theo ngày sinh chuẩn nhất">
                <Typography>
                  Trước tiên, chúng ta sẽ tìm hiểu cách tính Thần số học với các
                  chỉ số theo ngày sinh. Cách này đơn giản sẽ lấy các con số
                  trong ngày, tháng, năm sinh để tính ra 2 chỉ số chính gồm: con
                  số chủ đạo và chỉ số thái độ.
                </Typography>
                <Box
                  mt={1.25}
                  display={'flex'}
                  flexDirection={'column'}
                  rowGap={'15px'}
                >
                  <Typography
                    variant="h3"
                    component={'h4'}
                    className="font-philosopher"
                  >
                    Cách tính chỉ số đường đời (con số chủ đạo)
                  </Typography>
                  <Typography>
                    Các{' '}
                    <Typography component={'span'} color="primary">
                      con số chủ đạo
                    </Typography>{' '}
                    của mỗi người sẽ cung cấp các mô tả khái quát về tính cách,
                    điểm mạnh, điểm yếu, ngành nghề, hướng phát triển phù hợp
                    với mỗi cá nhân. Khi bạn cần phải khai phá các tiềm năng của
                    bản thân, con số chủ đạo sẽ đóng vai trò chủ chốt giúp bạn
                    thực hiện những điều này.
                  </Typography>
                  <Typography>
                    Công thức tính con số chủ đạo: CỘNG TẤT CẢ CÁC CON SỐ TRONG
                    NGÀY, THÁNG, NĂM SINH tới khi ĐƯỢC MỘT CHỮ SỐ TỪ 1-9.
                  </Typography>
                  <Typography>
                    Trường hợp đặc biệt: Bạn cộng ra số 11, 22, 33 thì đây được
                    gọi là những con số đặc biệt sẽ giữ nguyên 2 chữ số để tra
                    cứu.
                  </Typography>
                  <Box textAlign={'center'} my={2.5}>
                    <Box width={'fit-content'} margin={'0 auto'}>
                      <Box
                        component={'img'}
                        src="/assets/images/posts/cach_tinh_so_chu_dao.png"
                        alt="Thần số học là một môn khoa học đã có tuổi đời hơn 2500 năm"
                        sx={{ objectFit: 'cover' }}
                        width={'100%'}
                      />
                      <Typography
                        fontStyle={'italic'}
                        fontWeight={500}
                        mt={0.5}
                      >
                        Cách tính Thần số học cho con số chủ đạo
                      </Typography>
                    </Box>
                  </Box>
                  <Typography>Ví dụ: Bạn sinh ngày 02/09/2001.</Typography>
                  <Typography>
                    Áp dụng công thức tính số chủ đạo ta có: 0 + 2 + 0 + 9 + 2 +
                    0 + 0 + 1 = 5.
                  </Typography>
                  <Typography>Vậy 5 là con số chủ đạo của bạn.</Typography>
                </Box>
                <Box
                  mt={1.25}
                  display={'flex'}
                  flexDirection={'column'}
                  rowGap={2.5}
                >
                  <Typography
                    variant="h3"
                    component={'h4'}
                    className="font-philosopher"
                  >
                    Tính con số chủ đạo của bạn ngay
                  </Typography>
                  <Typography>Nhập Ngày/tháng/năm sinh của bạn:</Typography>
                  <RullingNumberForm />
                  <Typography
                    component={'i'}
                    fontSize={'1.25rem'}
                    textAlign={'center'}
                  >
                    Chúc bạn sớm khám phá ra chính mình!
                  </Typography>

                  <Box
                    mt={2}
                    display={'flex'}
                    flexDirection={'column'}
                    rowGap={'15px'}
                  >
                    <Typography
                      variant="h3"
                      component={'h4'}
                      className="font-philosopher"
                    >
                      Ý nghĩa của từng con số chủ đạo
                    </Typography>
                    <Box mt={2.5}>
                      <Grid container bgcolor={'#081D2D'}>
                        <Grid item xs={6} sm={8}>
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
                                sm={4}
                                md={3}
                                borderBottom={'2px solid #0E263B'}
                                borderRight={'2px solid #0E263B'}
                              >
                                <Box
                                  py={1}
                                  px={1.5}
                                  height={'76px'}
                                  textAlign={'center'}
                                >
                                  <Typography
                                    sx={{
                                      fontFamily: 'var(--philosopher-font)',
                                      fontSize: 16,
                                      lineHeight: 1,
                                    }}
                                  >
                                    Số
                                  </Typography>
                                  <Typography
                                    component={'span'}
                                    color="primary"
                                    sx={{
                                      fontFamily: 'var(--philosopher-font)',
                                      fontSize: 45,
                                      lineHeight: '50px',
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
                          sm={4}
                          sx={{
                            border: '2px solid #0E263B',
                            borderLeft: 0,
                            height: 'inherit',
                          }}
                        >
                          <Box py={1} px={1.5} height={'100%'}>
                            <Box>
                              <Typography
                                sx={{
                                  fontFamily: 'var(--philosopher-font)',
                                  fontSize: 16,
                                  lineHeight: 0,
                                }}
                              >
                                Số
                                <Typography
                                  component={'span'}
                                  color="primary"
                                  sx={{
                                    fontFamily: 'var(--philosopher-font)',
                                    fontSize: 45,
                                    fontWeight: 700,
                                    marginLeft: 1.5,
                                    lineHeight: '34px',
                                  }}
                                >
                                  1
                                </Typography>
                              </Typography>
                            </Box>
                            <Typography mt={2}>
                              Đại diện cho sự táo bạo, đổi mới, chấp nhận rủi
                              ro, khả năng phục hồi và đi theo tiếng nói bên
                              trong.
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                  </Box>

                  <Box
                    mt={2}
                    display={'flex'}
                    flexDirection={'column'}
                    rowGap={'15px'}
                  >
                    <Typography
                      variant="h3"
                      component={'h4'}
                      className="font-philosopher"
                    >
                      Cách tính chỉ số thái độ
                    </Typography>
                    <Typography>
                      Đây là chỉ số thể hiện thái độ, các phản ứng bản năng
                      trước một vấn đề, một dự án,…của bạn trong cuộc sống hàng
                      ngày. Các thái độ sẽ chỉ ra khả năng giải quyết tình
                      huống, vấn đề của bạn, giúp bạn có những góc nhìn tích cực
                      hơn.
                    </Typography>
                    <Typography>
                      Công thức tính{' '}
                      <Typography component={'span'} fontWeight={600}>
                        số thái độ: CỘNG NGÀY SINH và THÁNG SINH tới khi ĐƯỢC
                        MỘT CHỮ SỐ TỪ 1 – 9.
                      </Typography>
                    </Typography>
                    <Typography>Ví dụ: Bạn sinh ngày 02/09</Typography>
                    <Typography>
                      Áp dụng cách tính Thần số học chỉ số thái độ ta có: 0 + 2
                      + 0 + 9 = 11 = 1 + 1 = 2
                    </Typography>
                    <Typography>
                      Vậy{' '}
                      <Typography
                        component={'span'}
                        fontWeight={700}
                        color="primary"
                      >
                        2
                      </Typography>{' '}
                      là chỉ số thái độ của bạn.
                    </Typography>
                  </Box>
                </Box>
              </ContentDescriptionItem>
            </Box>
            <Divider
              sx={{
                mt: 3.75,
                mb: 3,
              }}
            />
          </Box>

          {/* Box Right */}
          <Box
            width={'400px'}
            maxWidth={'revert'}
            sx={{
              display: {
                xs: 'none',
                lg: 'block',
              },
            }}
          >
            <SearchNumerologyForm title="Tra cứu chỉ số của bản thân ngay" />
            <Divider
              sx={{
                mt: 3.75,
                mb: 3,
              }}
            />
            <Box ref={postRelatedRef}>
              <IconTwoRhombus />
              <Typography
                className="text-heading"
                sx={{ textTransform: 'uppercase' }}
              >
                BÀI VIẾT LIÊN QUAN
              </Typography>
              <Box
                mt={4}
                sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}
              >
                {relatedPosts.map((post) => (
                  <PostCard key={post.id} postInfo={post} />
                ))}
              </Box>
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
