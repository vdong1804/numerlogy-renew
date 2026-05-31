import { Box, Button, Container, Fab, Typography } from '@mui/material'
import * as React from 'react'

import { IconChevronBottom } from '@/components/icon'
import { getImageByMainNumber } from '@/utils/helpers'

export interface IBannerSearchResultPageProps {
  userInfo: {
    name: string
    birthday: string
    mainNumber: number
    isVip?: boolean
  }
}

export default function BannerSearchResultPage({
  userInfo: { name, birthday, mainNumber, isVip = false },
}: IBannerSearchResultPageProps) {
  return (
    <Box id="banner-search-result">
      <Container maxWidth={false}>
        <Box textAlign={'center'} py={5.5}>
          <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 1.25 }}>
            <Typography fontWeight={500} fontSize={'1.375rem'}>
              Báo cáo thần số học
            </Typography>
            <Typography
              className="name-teacher-heading"
              component={'span'}
              width={'fit-content'}
              margin={'0 auto'}
              textTransform={'capitalize'}
            >
              {name}
            </Typography>
            <Typography
              component={'span'}
              className="text-heading"
              color={'primary'}
              width={'fit-content'}
              margin={'0 auto'}
            >
              {birthday}
            </Typography>
          </Box>
          <Box mt={5}>
            <Typography
              sx={{
                display: 'block',
                margin: '0 auto',
                fontSize: '2.25rem',
                fontWeight: 700,
                color: '#44BBFF',
                textShadow: '0px 4px 13px rgba(27, 90, 251, 0.75)',
                width: 'fit-content',
              }}
              component={'span'}
            >
              SỐ CHỦ ĐẠO
            </Typography>
            <Box
              component={'img'}
              src={getImageByMainNumber(mainNumber)}
              width={'300px'}
            />
            {!isVip && (
              <Box
                px={2.25}
                py={1.25}
                borderRadius={2.5}
                sx={{
                  mx: 'auto',
                  width: {
                    xs: '95%',
                    md: '80%',
                    lg: '62.5%',
                  },
                  marginTop: -5,
                  backgroundColor: 'rgba(0, 168, 255, 0.07)',
                  backdropFilter: 'blur(6.5px)',
                }}
              >
                <Typography
                  variant="body2"
                  sx={{ fontStyle: 'italic', textAlign: 'left' }}
                >
                  Bạn đang sử dụng lượt tra miễn phí chỉ xem được giới hạn các
                  luận giải. Để xem những luận giải và giải pháp mà các chuyên
                  gia tại tracuuthansohoc.com đã nghiên cứu cho toàn bộ chỉ số
                  của bạn, vui lòng nâng cấp tài khoản VIP!
                </Typography>
                <Button variant="contained" sx={{ mt: 1.25 }}>
                  Nâng cấp vip
                </Button>
              </Box>
            )}
          </Box>
        </Box>
      </Container>
      <Box
        sx={{
          position: 'absolute',
          left: '50%',
          top: '100%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'rgba(1, 64, 101, 0.39)',
          borderRadius: '9999px',
        }}
        p={1}
      >
        <Fab
          aria-label="down"
          sx={{
            bgcolor: 'rgba(0, 90, 137, 0.38)',
            width: 65,
            height: 65,
          }}
          color="info"
        >
          <IconChevronBottom />
        </Fab>
      </Box>
    </Box>
  )
}
