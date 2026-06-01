import { Box, Container, Grid, IconButton, Typography } from '@mui/material'

import {
  IconEmail,
  IconFacebook,
  IconHome,
  IconInstagram,
  IconPhone,
  IconTiktok,
  IconTwitter,
  IconYoutube,
} from '@/components/icon'

/** Legal pages + navigation links shown in footer "Thông tin chung" column */
const LEGAL_LINKS = [
  { label: 'Câu hỏi thường gặp', href: '/faq' },
  { label: 'Hướng dẫn sử dụng', href: '/huong-dan' },
  { label: 'Chính sách bảo mật', href: '/privacy' },
  { label: 'Điều khoản sử dụng', href: '/terms' },
  { label: 'Chính sách hoàn tiền', href: '/refund-policy' },
  { label: 'Liên hệ', href: '/contact' },
]

const CURRENT_YEAR = new Date().getFullYear()
const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION ?? 'v3'

const LIST_SOCIAL = [
  {
    id: 1,
    icon: <IconFacebook />,
    to: '#',
  },
  {
    id: 2,
    icon: <IconTwitter />,
    to: '#',
  },
  {
    id: 3,
    icon: <IconInstagram />,
    to: '#',
  },
  {
    id: 4,
    icon: <IconTiktok />,
    to: '#',
  },
  {
    id: 5,
    icon: <IconYoutube />,
    to: '#',
  },
]
export default function Footer() {
  return (
    <Box component={'footer'}>
      <Box bgcolor={'var(--bg-secondary)'} paddingTop={5.5} paddingBottom={7.5}>
        <Container maxWidth={false}>
          <Grid container columnSpacing={3}>
            <Grid item xs={12} sm={6} lg={4}>
              <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 3 }}>
                <Box>
                  <img src="/numerology_logo.svg" alt="Logo" />
                </Box>
                <Typography variant="body2">
                  Công cụ được tùy chỉnh theo ngày sinh và tên chính xác của bạn
                  … Vì vậy, hãy lưu ý: thông tin bạn sắp nhận được có thể khiến
                  bạn bị sốc.
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    marginTop: -1.5,
                  }}
                >
                  {LIST_SOCIAL.map(({ id, icon, to }) => (
                    <Box key={id} component={'a'} href={to}>
                      <IconButton
                        sx={{
                          p: 1.5,
                          '&:hover': {
                            transform: 'scale(1.3)',
                            transition: 'all ease 0.3s',
                            filter: 'brightness(0.6)',
                          },
                        }}
                      >
                        {icon}
                      </IconButton>
                    </Box>
                  ))}
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} lg={2}>
              <Box mt={2.5}>
                <Typography variant="h4" component="h4">
                  Thông tin chung
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    rowGap: '10px',
                    mt: 2.5,
                  }}
                >
                  {LEGAL_LINKS.map(({ label, href }) => (
                    <Typography
                      key={label}
                      variant="body2"
                      component="a"
                      color={'inherit'}
                      width={'fit-content'}
                      href={href}
                      sx={{
                        '&:hover': {
                          color: 'var(--text-main)',
                          transition: 'all ease 0.2s',
                        },
                      }}
                    >
                      {label}
                    </Typography>
                  ))}
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Box mt={2.5}>
                <Typography variant="h4" component="h4">
                  Liên hệ với chúng tôi
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    rowGap: 2.5,
                    mt: 2.5,
                    alignItems: 'center',
                    columnGap: 0.5,
                    flexWrap: {
                      xs: 'wrap',
                      sm: 'nowrap',
                      lg: 'nowrap',
                    },
                  }}
                >
                  <Box
                    sx={{
                      width: {
                        xs: '100%',
                        lg: 'auto',
                      },
                    }}
                  >
                    <Box
                      component={'iframe'}
                      src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d10631.852165994946!2d105.85775363263471!3d21.02202322369023!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3135abebf87e0011%3A0x647af200da508d2b!2zTmjDoCBow6F0IEzhu5tuIEjDoCBO4buZaQ!5e0!3m2!1svi!2s!4v1681199970435!5m2!1svi!2s"
                      width={'100%'}
                      minWidth={'250px'}
                      height={'100%'}
                      borderRadius={'5px'}
                      allowFullScreen={true}
                      loading="lazy"
                      referrerPolicy="no-referrer-when-downgrade"
                    ></Box>
                  </Box>
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      rowGap: 1,
                      width: {
                        xs: '100%',
                        lg: '50%',
                      },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <IconButton>
                        <IconHome />
                      </IconButton>

                      <Typography variant="body2">
                        Địa chỉ: 123 Hai Bà Trưng, Hà Nội
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <IconButton>
                        <IconPhone />
                      </IconButton>

                      <Typography variant="body2">
                        Điện thoại: 123 456 789
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <IconButton>
                        <IconEmail />
                      </IconButton>

                      <Typography variant="body2">
                        Liên hệ hợp tác: admin@gmail.com
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>
      <Typography
        variant="body2"
        sx={{
          textAlign: 'center',
          paddingTop: 3,
          paddingBottom: 2.5,
          color: 'text.secondary',
        }}
      >
        &copy; {CURRENT_YEAR} nhansinhquan.vn · All rights reserved · {APP_VERSION}
      </Typography>
    </Box>
  )
}
