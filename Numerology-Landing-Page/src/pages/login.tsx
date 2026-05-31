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
import { postJson } from '@/lib/user-api'
import type { TokenPair } from '@/lib/user-auth'
import { setUserTokens } from '@/lib/user-auth'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setServerError('')
    try {
      const tokens = await postJson<TokenPair>('/auth/login', data)
      setUserTokens(tokens)
      const next = typeof router.query.next === 'string' ? router.query.next : '/'
      router.replace(next)
    } catch (err) {
      setServerError((err as Error).message || 'Đăng nhập thất bại')
    }
  }

  return (
    <>
      <Head>
        <title>Đăng nhập · Numerology</title>
      </Head>
      <AuthShell
        title="Đăng nhập"
        subtitle="Truy cập tài khoản Numerology của bạn"
      >
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
            <AuthTextField
              label="Mật khẩu"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowPassword((v) => !v)}
                      edge="end"
                      sx={{ color: 'rgba(255,255,255,0.7)' }}
                    >
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              {...register('password', { required: 'Vui lòng nhập mật khẩu' })}
            />

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
              disabled={isSubmitting}
              startIcon={isSubmitting ? <CircularProgress size={18} color="inherit" /> : null}
              sx={{ py: 1.4, fontSize: '1rem' }}
            >
              {isSubmitting ? 'Đang xử lý…' : 'Đăng nhập'}
            </Button>

            <Box display="flex" justifyContent="space-between" mt={1}>
              <Link href="/forgot-password" passHref legacyBehavior>
                <Typography
                  component="a"
                  variant="body2"
                  sx={{
                    color: 'rgba(255,255,255,0.85)',
                    textDecoration: 'none',
                    '&:hover': { color: '#F96A2D' },
                  }}
                >
                  Quên mật khẩu?
                </Typography>
              </Link>
              <Link href="/register" passHref legacyBehavior>
                <Typography
                  component="a"
                  variant="body2"
                  sx={{
                    color: 'rgba(255,255,255,0.85)',
                    textDecoration: 'none',
                    fontWeight: 600,
                    '&:hover': { color: '#F96A2D' },
                  }}
                >
                  Tạo tài khoản
                </Typography>
              </Link>
            </Box>
          </Stack>
        </Box>
      </AuthShell>
    </>
  )
}
