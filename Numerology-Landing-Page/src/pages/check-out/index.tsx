import { Box, Container, Grid, Typography } from '@mui/material'
import type { ReactElement } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import { BankInfo, TotalBill } from '@/modules/checkout'

const CheckoutPage: NextPageWithLayout = () => {
  return (
    <Container maxWidth={false}>
      <Box component={'h1'} my={4}>
        Hướng dẫn thanh toán cho đơn hàng IRLWWR
      </Box>
      <Grid container spacing={4}>
        <Grid item xs={12} md={7}>
          <BankInfo />
        </Grid>
        <Grid item xs={12} md={5}>
          <TotalBill />
        </Grid>
      </Grid>
      <Typography mt={3} mb={8} fontWeight={500}>
        Bạn có thắc mắc ? Liên hệ ngay:{' '}
        <Typography component="span" color="primary" fontWeight={600}>
          0339387373
        </Typography>
      </Typography>
    </Container>
  )
}
CheckoutPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta title="Thông tin thanh toán" description="Thông tin thanh toán" />
      }
    >
      {page}
    </Main>
  )
}

export default CheckoutPage
