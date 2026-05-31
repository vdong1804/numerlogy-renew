import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material'
import Head from 'next/head'
import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import AuthShell from '@/components/auth/auth-shell'
import AuthTextField from '@/components/auth/auth-text-field'
import TurnstileWidget from '@/components/turnstile-widget'
import { postJson } from '@/lib/user-api'

interface ForgotPasswordForm {
  email: string
}

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false)
  const [serverError, setServerError] = useState('')
  const [captchaToken, setCaptchaToken] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordForm>()

  const onSubmit = async (data: ForgotPasswordForm) => {
    setServerError('')
    try {
      await postJson('/auth/forgot-password', { email: data.email, captcha_token: captchaToken })
      setSubmitted(true)
    } catch (err) {
      setServerError((err as Error).message || 'Không thể gửi email lúc này')
    }
  }

  return (
    <>
      <Head>
        <title>Quên mật khẩu · Numerology</title>
      </Head>
      <AuthShell
        title="Quên mật khẩu"
        subtitle="Nhập email tài khoản, chúng tôi sẽ gửi liên kết đặt lại mật khẩu."
      >
        {submitted ? (
          <Stack spacing={2.5}>
            <Alert severity="success" variant="filled">
              Nếu email tồn tại trong hệ thống, một liên kết đặt lại mật khẩu đã
              được gửi. Vui lòng kiểm tra hộp thư của bạn.
            </Alert>
            <Link href="/login" passHref legacyBehavior>
              <Button
                variant="outlined"
                component="a"
                fullWidth
                sx={{
                  color: '#fff',
                  borderColor: 'rgba(255,255,255,0.5)',
                  '&:hover': {
                    borderColor: '#F96A2D',
                    backgroundColor: 'rgba(249,106,45,0.08)',
                  },
                }}
              >
                Quay lại đăng nhập
              </Button>
            </Link>
          </Stack>
        ) : (
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2.5}>
              <AuthTextField
                label="Email"
                type="email"
                autoComplete="username"
                error={Boolean(errors.email)}
                helperText={errors.email?.message}
                {...register('email', {
                  required: 'Vui lòng nhập email',
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: 'Email không hợp lệ',
                  },
                })}
              />

              <TurnstileWidget onSuccess={setCaptchaToken} theme="dark" />

              {serverError && (
                <Alert severity="error" variant="filled">
                  {serverError}
                </Alert>
              )}

              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                disabled={isSubmitting || !captchaToken}
                startIcon={isSubmitting ? <CircularProgress size={18} color="inherit" /> : null}
                sx={{ py: 1.4, fontSize: '1rem' }}
              >
                {isSubmitting ? 'Đang xử lý…' : 'Gửi liên kết đặt lại'}
              </Button>

              <Typography variant="body2" textAlign="center">
                <Link href="/login" passHref legacyBehavior>
                  <Typography
                    component="a"
                    variant="body2"
                    sx={{
                      color: 'rgba(255,255,255,0.85)',
                      textDecoration: 'none',
                      '&:hover': { color: '#F96A2D' },
                    }}
                  >
                    Quay lại đăng nhập
                  </Typography>
                </Link>
              </Typography>
            </Stack>
          </Box>
        )}
      </AuthShell>
    </>
  )
}
