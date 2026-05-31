/**
 * Trang Liên hệ — SSG, tiếng Việt.
 * Form submit chỉ alert "Vui lòng email trực tiếp" (backend endpoint chưa có).
 * Placeholders [BRACKETS] để user search & replace.
 */
import {
  Alert,
  Box,
  Button,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material'
import type { GetStaticProps } from 'next'
import { useState } from 'react'

import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

const FIELD_SX = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 2,
    bgcolor: 'rgba(255,255,255,0.04)',
    color: '#fff',
    maxWidth: 'unset',
    '& fieldset': { borderColor: 'rgba(255,255,255,0.18)' },
    '&:hover fieldset': { borderColor: '#F96A2D !important' },
  },
  '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
  '& .MuiInputBase-input': { padding: '12px 14px' },
}

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    alert(
      'Cảm ơn bạn! Vui lòng gửi email trực tiếp đến [EMAIL HỖ TRỢ] để được phản hồi nhanh nhất.'
    )
    setSubmitted(true)
  }

  return (
    <Main
      meta={
        <Meta
          title="Liên hệ | Nhân Sinh Quán"
          description="Liên hệ với đội ngũ hỗ trợ Nhân Sinh Quán — hotline, email, Zalo OA"
        />
      }
    >
      <PageShell
        title="Liên hệ với chúng tôi"
        subtitle="Đội ngũ Nhân Sinh Quán luôn sẵn sàng đồng hành. Hãy chọn kênh thuận tiện nhất cho bạn."
        maxWidth="lg"
        bare
      >
        <Grid container spacing={{ xs: 3, md: 4 }}>
          {/* Info block */}
          <Grid item xs={12} md={5}>
            <Box
              sx={{
                p: { xs: 3, md: 4 },
                borderRadius: 4,
                bgcolor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.10)',
                backdropFilter: 'blur(10px)',
                height: '100%',
              }}
            >
              <Typography
                component="h2"
                sx={{
                  fontFamily: 'var(--philosopher-font)',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  mb: 3,
                }}
              >
                Thông tin liên hệ
              </Typography>

              <InfoRow label="Tên doanh nghiệp" value="[TÊN DOANH NGHIỆP]" />
              <InfoRow label="MST / GPKD" value="[MST / SỐ GPKD]" />
              <InfoRow label="Địa chỉ" value="[ĐỊA CHỈ ĐẦY ĐỦ]" />
              <InfoRow label="Hotline" value="[SỐ ĐIỆN THOẠI]" />
              <InfoRow label="Email hỗ trợ" value="[EMAIL HỖ TRỢ]" isEmail />
              <InfoRow label="Zalo OA" value="[ZALO OA LINK]" isLink />

              <Box
                sx={{
                  mt: 3,
                  p: 2,
                  borderRadius: 2,
                  bgcolor: 'rgba(249,106,45,0.10)',
                  border: '1px solid rgba(249,106,45,0.25)',
                  fontSize: '0.88rem',
                  lineHeight: 1.7,
                }}
              >
                <strong>Giờ làm việc</strong>
                <br />
                Thứ 2 – Thứ 6: 8:00 – 17:30
                <br />
                Thứ 7: 8:00 – 12:00
                <br />
                Chủ nhật &amp; Lễ: nghỉ
              </Box>
            </Box>
          </Grid>

          {/* Contact form */}
          <Grid item xs={12} md={7}>
            <Box
              sx={{
                p: { xs: 3, md: 4 },
                borderRadius: 4,
                bgcolor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.10)',
                backdropFilter: 'blur(10px)',
                height: '100%',
              }}
            >
              <Typography
                component="h2"
                sx={{
                  fontFamily: 'var(--philosopher-font)',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  mb: 3,
                }}
              >
                Gửi tin nhắn
              </Typography>

              {submitted ? (
                <Alert
                  severity="success"
                  sx={{
                    bgcolor: 'rgba(34,197,94,0.12)',
                    color: '#A7F3D0',
                    border: '1px solid rgba(34,197,94,0.3)',
                    '& .MuiAlert-icon': { color: '#A7F3D0' },
                  }}
                >
                  Cảm ơn bạn đã liên hệ! Vui lòng gửi email trực tiếp đến{' '}
                  <strong>[EMAIL HỖ TRỢ]</strong> để được phản hồi nhanh nhất.
                </Alert>
              ) : (
                <Box
                  component="form"
                  onSubmit={handleSubmit}
                  sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
                >
                  <TextField
                    name="name"
                    label="Họ và tên *"
                    placeholder="Nguyễn Văn A"
                    required
                    fullWidth
                    sx={FIELD_SX}
                  />
                  <TextField
                    name="email"
                    type="email"
                    label="Email *"
                    placeholder="example@email.com"
                    required
                    fullWidth
                    sx={FIELD_SX}
                  />
                  <FormControl fullWidth sx={FIELD_SX} required>
                    <InputLabel id="cf-subject-label">Chủ đề *</InputLabel>
                    <Select
                      labelId="cf-subject-label"
                      name="subject"
                      defaultValue=""
                      label="Chủ đề *"
                      sx={{
                        color: '#fff',
                        '& .MuiSvgIcon-root': { color: '#fff' },
                      }}
                    >
                      <MenuItem value="order">Hỗ trợ đơn hàng</MenuItem>
                      <MenuItem value="refund">Yêu cầu hoàn tiền</MenuItem>
                      <MenuItem value="technical">Lỗi kỹ thuật</MenuItem>
                      <MenuItem value="partnership">Hợp tác / Affiliate</MenuItem>
                      <MenuItem value="other">Khác</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    name="message"
                    label="Nội dung *"
                    placeholder="Mô tả vấn đề hoặc câu hỏi của bạn..."
                    required
                    multiline
                    minRows={5}
                    fullWidth
                    sx={FIELD_SX}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    size="large"
                    sx={{ alignSelf: 'flex-start', mt: 1 }}
                  >
                    Gửi tin nhắn
                  </Button>
                </Box>
              )}
            </Box>
          </Grid>
        </Grid>
      </PageShell>
    </Main>
  )
}

function InfoRow({
  label,
  value,
  isEmail,
  isLink,
}: {
  label: string
  value: string
  isEmail?: boolean
  isLink?: boolean
}) {
  return (
    <Box sx={{ mb: 1.75 }}>
      <Typography
        sx={{
          color: 'rgba(255,255,255,0.55)',
          fontSize: '0.78rem',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          mb: 0.25,
        }}
      >
        {label}
      </Typography>
      {isEmail ? (
        <a href={`mailto:${value}`} style={{ color: '#F96A2D', fontWeight: 500 }}>
          {value}
        </a>
      ) : isLink ? (
        <a
          href={value}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#F96A2D', fontWeight: 500 }}
        >
          {value}
        </a>
      ) : (
        <Typography sx={{ color: '#fff', fontSize: '0.95rem' }}>{value}</Typography>
      )}
    </Box>
  )
}

export const getStaticProps: GetStaticProps = async () => ({ props: {} })
