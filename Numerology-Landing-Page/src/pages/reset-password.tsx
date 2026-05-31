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

interface ResetPasswordForm {
  new_password: string
  confirm_password: string
}

export default function ResetPasswordPage() {
  const router = useRouter()
  const token = typeof router.query.token === 'string' ? router.query.token : ''
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const [success, setSuccess] = useState(false)
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordForm>()

  const newPassword = watch('new_password')

  const onSubmit = async (data: ResetPasswordForm) => {
    setServerError('')
    if (!token) {
      setServerError('Thiếu mã đặt lại. Vui lòng truy cập lại từ email.')
      return
    }
    try {
      await postJson('/auth/reset-password', {
        token,
        new_password: data.new_password,
      })
      setSuccess(true)
      setTimeout(() => router.replace('/login'), 1500)
    } catch (err) {
      setServerError((err as Error).message || 'Không thể đặt lại mật khẩu')
    }
  }

  return (
    <>
      <Head>
        <title>Đặt lại mật khẩu · Numerology</title>
      </Head>
      <AuthShell
        title="Đặt lại mật khẩu"
        subtitle="Nhập mật khẩu mới của bạn dưới đây."
      >
        {success ? (
          <Stack spacing={2.5}>
            <Alert severity="success" variant="filled">
              Đặt lại mật khẩu thành công. Đang chuyển đến trang đăng nhập…
            </Alert>
          </Stack>
        ) : (
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2.5}>
              <AuthTextField
                label="Mật khẩu mới"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                error={Boolean(errors.new_password)}
                helperText={errors.new_password?.message ?? 'Tối thiểu 8 ký tự'}
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
                {...register('new_password', {
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
                  validate: (v) => v === newPassword || 'Mật khẩu không khớp',
                })}
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
                disabled={isSubmitting || !token}
                startIcon={isSubmitting ? <CircularProgress size={18} color="inherit" /> : null}
                sx={{ py: 1.4, fontSize: '1rem' }}
              >
                {isSubmitting ? 'Đang xử lý…' : 'Cập nhật mật khẩu'}
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
