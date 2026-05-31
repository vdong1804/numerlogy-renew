import { Box, Grid, Typography } from '@mui/material'
import { useRouter } from 'next/router'
import * as React from 'react'

import { convertToVND } from '@/utils/helpers'

import { TitleItem } from './parts'

export default function TotalBill() {
  const router = useRouter()
  return (
    <Box
      sx={{
        p: 3,
        borderRadius: 5,
        boxShadow: '0 15px 25px -5px rgba(211, 211, 211, 0.25)',
        bgcolor: 'common.white',
      }}
    >
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TitleItem>Xem lại đơn hàng</TitleItem>
          <Typography
            sx={{ fontWeight: 600, fontSize: 18, color: 'text.secondary' }}
          >
            IRLWWR
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <TitleItem>Phương thức thanh toán</TitleItem>
          <Typography
            sx={{ fontWeight: 600, fontSize: 18, color: 'text.secondary' }}
          >
            Chuyển khoản
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Box borderRadius={2} p={2.5} bgcolor="#F6F7FB">
            <TitleItem>Khách hàng</TitleItem>
            <Typography
              sx={{
                fontWeight: 700,
                fontSize: 24,
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Khải
            </Typography>
            <Typography sx={{ fontSize: 18, color: 'text.secondary' }}>
              vukhaiabc@gmail.com
            </Typography>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box width={100} height={100}>
              <Box
                component="img"
                src={`${router.basePath}/assets/images/logo-vip.png`}
                width={'100%'}
                sx={{
                  objectFit: 'cover',
                }}
                alt="Logo vip member"
              />
            </Box>

            <Box mt={2}>
              <Typography
                sx={{ mb: 1, fontSize: 18, fontWeight: 700 }}
                color="text.secondary"
              >
                Đăng kí thành viên VIP
              </Typography>

              <Typography
                component="span"
                color="primary"
                sx={{ fontSize: 18, fontWeight: 500 }}
              >
                {convertToVND(999000)}
              </Typography>
              <Typography
                component="span"
                ml={1}
                color="text.secondary"
                sx={{
                  fontSize: 14,
                  fontStyle: 'italic',
                  textDecoration: 'line-through',
                }}
              >
                {convertToVND(1100000)}
              </Typography>
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Typography
            sx={{
              color: (theme) => theme.palette.primary.main,
              mx: -3,
              mb: -3,
              fontSize: 20,
              fontWeight: 700,
              bgcolor: 'grey.200',
              py: 2,
              display: 'flex',
              justifyContent: 'center',
              borderBottomRightRadius: 20,
              borderBottomLeftRadius: 20,
            }}
          >
            Tổng cộng: {convertToVND(999000)}
          </Typography>
        </Grid>
      </Grid>
    </Box>
  )
}
