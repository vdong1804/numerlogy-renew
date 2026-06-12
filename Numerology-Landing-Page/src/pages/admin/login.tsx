/**
 * Admin login — split layout w/ gradient hero panel + form card.
 * POST /auth/login → verify is_superuser → store admin_access_token
 */
import Head from 'next/head'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { AlertCircle, ArrowRight, Eye, EyeOff, Lock, Mail, ShieldCheck, Sparkles, Zap } from 'lucide-react'

import { AdminThemeProvider } from '@/components/admin/admin-theme-provider'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { clearAdminToken, getJson, setAdminTokens } from '@/lib/admin-api'
import type { AdminUser } from '@/lib/admin-auth'

interface LoginForm {
  email: string
  password: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
}

export default function AdminLoginPage() {
  const router = useRouter()
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const { register, handleSubmit, formState: { isSubmitting, errors } } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setError('')
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'}/auth/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: data.email, password: data.password }),
        }
      )
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const detail = body?.detail
        const msg = typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((e: { msg?: string }) => e.msg ?? '').filter(Boolean).join('; ')
            : 'Đăng nhập thất bại'
        throw new Error(msg)
      }
      const token = (await res.json()) as TokenResponse
      setAdminTokens(token.access_token, token.refresh_token)

      const me = await getJson<AdminUser>('/auth/me')
      if (!me.is_superuser) {
        clearAdminToken()
        throw new Error('Tài khoản không có quyền admin')
      }
      router.replace('/admin')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <AdminThemeProvider>
      <Head><title>Đăng nhập · Admin Numerology</title></Head>
      <div className="admin-shell min-h-screen bg-background grid lg:grid-cols-[1.05fr_1fr] xl:grid-cols-2">
        {/* Hero panel */}
        <div className="relative hidden lg:flex flex-col justify-between p-12 xl:p-16 text-white overflow-hidden">
          {/* Layered gradient */}
          <div className="absolute inset-0 bg-[linear-gradient(135deg,#6366f1_0%,#8b5cf6_45%,#ec4899_100%)]" />
          {/* Soft white radial blobs */}
          <div className="absolute inset-0 opacity-40 [background:radial-gradient(circle_at_15%_20%,rgba(255,255,255,0.55)_0%,transparent_40%),radial-gradient(circle_at_85%_70%,rgba(255,255,255,0.35)_0%,transparent_35%)]" />
          {/* Subtle grid texture */}
          <div className="absolute inset-0 opacity-[0.08] [background-image:linear-gradient(white_1px,transparent_1px),linear-gradient(90deg,white_1px,transparent_1px)] [background-size:32px_32px]" />

          <div className="relative z-10 flex items-center gap-3">
            <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-white/15 backdrop-blur ring-1 ring-white/30 shadow-lg">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-base font-semibold">Numerology</span>
              <span className="text-[11px] uppercase tracking-[0.18em] text-white/70">Admin Console</span>
            </div>
          </div>

          <div className="relative z-10 max-w-md">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 backdrop-blur px-2.5 py-1 text-[11px] font-medium ring-1 ring-white/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Hệ thống hoạt động bình thường
            </span>
            <h2 className="mt-5 text-4xl xl:text-5xl font-bold leading-[1.1] tracking-tight">
              Quản lý nội dung
              <br />
              <span className="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                Thần Số Học
              </span>{' '}
              tinh gọn
            </h2>
            <p className="mt-5 text-sm xl:text-base text-white/80 leading-relaxed">
              Theo dõi thanh toán, phê duyệt giao dịch, quản lý người dùng và biên tập
              23 bảng nội dung — tất cả trong một dashboard hiện đại.
            </p>

            <div className="mt-9 grid grid-cols-3 gap-3">
              {[
                { icon: Zap, label: 'Tức thì', desc: 'CRUD realtime' },
                { icon: ShieldCheck, label: 'An toàn', desc: 'JWT + RBAC' },
                { icon: Sparkles, label: 'Tinh tế', desc: 'UI hiện đại' },
              ].map((f) => (
                <div
                  key={f.label}
                  className="rounded-xl bg-white/10 backdrop-blur-md border border-white/15 px-3 py-3 hover:bg-white/15 transition-colors"
                >
                  <f.icon className="w-4 h-4 text-white/90" />
                  <p className="mt-2 text-[13px] font-semibold">{f.label}</p>
                  <p className="text-[11px] text-white/65">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <p className="relative z-10 text-xs text-white/70">
            © {new Date().getFullYear()} Numerology Platform · v1.0
          </p>
        </div>

        {/* Form */}
        <div className="relative flex items-center justify-center p-6 sm:p-12 bg-background admin-gradient-mesh">
          <Card className="w-full max-w-md p-8 sm:p-10 rounded-2xl border-border/60 shadow-[0_20px_60px_-20px_rgba(80,72,229,0.25)]">
            <div className="flex flex-col items-center text-center mb-8">
              <div className="lg:hidden mb-4 flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary via-violet-500 to-pink-500 text-white shadow-lg ring-1 ring-white/40">
                <Sparkles className="w-6 h-6" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight">Đăng nhập quản trị</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Đăng nhập bằng tài khoản admin để tiếp tục
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-[13px]">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    placeholder="admin@example.com"
                    className="h-11 pl-10 rounded-lg"
                    {...register('email', { required: 'Vui lòng nhập email' })}
                  />
                </div>
                {errors.email && (
                  <p className="text-xs text-destructive">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-[13px]">Mật khẩu</Label>
                  <a href="mailto:support@example.com" className="text-[11px] text-muted-foreground hover:text-primary transition-colors">
                    Quên mật khẩu?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="Nhập mật khẩu của bạn"
                    className="h-11 pl-10 pr-10 rounded-lg"
                    {...register('password', { required: 'Vui lòng nhập mật khẩu' })}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 inline-flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              {error && (
                <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive animate-fade-in">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="group relative w-full h-12 rounded-lg overflow-hidden text-sm font-semibold text-white shadow-[0_8px_24px_-8px_rgba(80,72,229,0.55)] transition-all duration-200 hover:shadow-[0_12px_28px_-8px_rgba(80,72,229,0.7)] hover:-translate-y-px active:translate-y-0 disabled:opacity-60 disabled:pointer-events-none disabled:hover:translate-y-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                <span className="absolute inset-0 bg-[linear-gradient(120deg,#6366f1_0%,#8b5cf6_55%,#a855f7_100%)]" />
                <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-[linear-gradient(120deg,#7c3aed_0%,#a855f7_55%,#ec4899_100%)]" />
                <span className="relative z-10 inline-flex items-center justify-center gap-2">
                  {isSubmitting ? (
                    <>
                      <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
                      Đang đăng nhập...
                    </>
                  ) : (
                    <>
                      Đăng nhập
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </span>
              </button>
            </form>

            <div className="relative my-6 flex items-center">
              <span className="flex-1 h-px bg-border" />
              <span className="px-3 text-[10px] uppercase tracking-widest text-muted-foreground">
                Bảo mật
              </span>
              <span className="flex-1 h-px bg-border" />
            </div>

            <p className="text-center text-xs text-muted-foreground">
              Phiên đăng nhập được bảo vệ bằng JWT.{' '}
              <a href="mailto:support@example.com" className="text-primary font-medium hover:underline">
                Liên hệ hỗ trợ
              </a>
            </p>
          </Card>
        </div>
      </div>
    </AdminThemeProvider>
  )
}
