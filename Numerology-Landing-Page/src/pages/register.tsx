import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  InputAdornment,
  Stack,
  Typography,
} from '@mui/material'
import Head from 'next/head'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import AuthShell from '@/components/auth/auth-shell'
import AuthTextField from '@/components/auth/auth-text-field'
import TurnstileWidget from '@/components/turnstile-widget'
import { postJson } from '@/lib/user-api'
import type { TokenPair } from '@/lib/user-auth'
import { setUserTokens } from '@/lib/user-auth'

interface RegisterForm {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export default function RegisterPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const [captchaToken, setCaptchaToken] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>()

  const password = watch('password')

  const onSubmit = async (data: RegisterForm) => {
    setServerError('')
    try {
      const tokens = await postJson<TokenPair>('/auth/register', {
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        captcha_token: captchaToken,
      })
      setUserTokens(tokens)
      router.replace('/')
    } catch (err) {
      setServerError((err as Error).message || 'Đăng ký thất bại')
    }
  }

  return (
    <>
      <Head>
        <title>Đăng ký · Numerology</title>
      </Head>
      <AuthShell
        title="Tạo tài khoản"
        subtitle="Đăng ký để truy cập đầy đủ tính năng Thần Số Học"
      >
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <Stack spacing={2.5}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <AuthTextField
                label="Họ"
                error={Boolean(errors.last_name)}
                helperText={errors.last_name?.message}
                {...register('last_name', { required: 'Vui lòng nhập họ' })}
              />
              <AuthTextField
                label="Tên"
                error={Boolean(errors.first_name)}
                helperText={errors.first_name?.message}
                {...register('first_name', { required: 'Vui lòng nhập tên' })}
              />
            </Stack>

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

            <AuthTextField
              label="Mật khẩu"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message ?? 'Tối thiểu 8 ký tự'}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword((v) => !v)}
                      edge="end"
                      aria-label="toggle password visibility"
                      sx={{ color: 'rgba(255,255,255,0.7)' }}
                    >
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              {...register('password', {
                required: 'Vui lòng nhập mật khẩu',
                minLength: { value: 8, message: 'Tối thiểu 8 ký tự' },
              })}
            />

            <AuthTextField
              label="Xác nhận mật khẩu"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              error={Boolean(errors.confirm_password)}
              helperText={errors.confirm_password?.message}
              {...register('confirm_password', {
                required: 'Vui lòng xác nhận mật khẩu',
                validate: (v) => v === password || 'Mật khẩu không khớp',
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
              {isSubmitting ? 'Đang xử lý…' : 'Tạo tài khoản'}
            </Button>

            <Typography
              variant="body2"
              textAlign="center"
              sx={{ color: 'rgba(255,255,255,0.75)' }}
            >
              Đã có tài khoản?{' '}
              <Link href="/login" passHref legacyBehavior>
                <Typography
                  component="a"
                  variant="body2"
                  sx={{
                    color: '#F96A2D',
                    fontWeight: 600,
                    textDecoration: 'none',
                  }}
                >
                  Đăng nhập
                </Typography>
              </Link>
            </Typography>
          </Stack>
        </Box>
      </AuthShell>
    </>
  )
}
