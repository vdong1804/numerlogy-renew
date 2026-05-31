import { Box, Container, Grid, Typography } from '@mui/material'

import { SearchNumerologyForm } from '@/components/form'

import { CommentForNumerology } from './parts'

export default function LookUpNumerology() {
  return (
    <Box className="lookup-numerology" id="tra-cuu" py={4}>
      <Container maxWidth={false}>
        <Grid
          container
          rowGap={4}
          justifyContent={'center'}
          alignItems={'center'}
        >
          <Grid item xs={12} md={5} lg={6}>
            <Box
              maxWidth={'490px'}
              margin={'0 auto'}
              sx={{
                display: {
                  xs: 'none',
                  md: 'flex',
                },
              }}
            >
              <img width={'100%'} src="/assets/images/satellite.png" alt="Hình minh họa tra cứu thần số học" />
            </Box>
          </Grid>
          <Grid item xs={12} md={7} lg={6}>
            <Box
              sx={{
                marginTop: 1,
                marginLeft: {
                  md: 8,
                },
              }}
            >
              <SearchNumerologyForm
                title="Xem thần số học online"
                subTitle="Aladanh Thành"
              />
            </Box>
          </Grid>
          <Grid item xs={12}>
            <Box
              maxWidth={'1110px'}
              mx={'auto'}
              sx={{
                p: {
                  xs: 2,
                  lg: 4,
                },
              }}
              border={'1px solid #222F36'}
              borderRadius={'5px'}
            >
              <Typography className="text-heading" component={'h3'}>
                Chú thích
              </Typography>
              <Box
                display={'flex'}
                flexDirection={'column'}
                rowGap={2.5}
                mt={2}
              >
                <Typography>
                  Nếu ngày sinh trên giấy tờ (chứng minh thư, bằng lái, khai
                  sinh…) của bạn khác với ngày sinh dương lịch thật thì cuộc đời
                  bạn sẽ có sự xáo trộn từ cả 2 ngày sinh này. Bạn nên tra cứu
                  cả 2 để biết thêm chi tiết, tuy nhiên kết quả sẽ thiên về ngày
                  sinh dương lịch thật!
                </Typography>
                <Typography>
                  Tên thường dùng là tên mà mọi người thường gọi bạn hoặc một
                  danh xưng bạn thường dùng, tên này sẽ bù trừ vào biểu đồ ngày
                  sinh của bạn. Nếu bạn không có tên thường dùng, hệ thống sẽ tự
                  lấy họ tên khai sinh của bạn để tính toán trong biểu đồ tổng
                  hợp.
                </Typography>
                <Typography>
                  Số chủ đạo tuy rất quan trọng nhưng không thể hiện hết thông
                  tin thần số học của bạn. Để xem kết quả tra cứu chính xác, hãy
                  kết hợp tất cả các chỉ số mà chúng tôi tính toán!
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} mt={4}>
            <CommentForNumerology />
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
