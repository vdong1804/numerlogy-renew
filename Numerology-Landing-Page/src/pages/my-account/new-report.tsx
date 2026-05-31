/**
 * /my-account/new-report — generate a personalized PDF report inside the account area.
 *
 * UX: user submits họ tên + ngày sinh + SĐT, server renders PDF via
 * GET /api/so-hoc and decrements UserProfile.number_download by 1.
 * Page shows live quota remaining and disables submit at quota=0.
 *
 * Why this exists: previously the only path to spend quota was the homepage
 * search form → /ket-qua → "Tải PDF" — invisible to a user who just bought a
 * package and lands in /my-account. This page closes the loop.
 */
import dayjs from 'dayjs'
import { Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { getDashboard, type MyDashboardSummary } from '@/lib/my-account-api'

import numerologyApi from '../api/numerologyApi'

const FIELD_CLS = 'h-10 bg-muted/40'

interface FormState {
  name: string
  sex: '1' | '2'
  birth_day: string  // ISO yyyy-mm-dd from <input type="date">
  phone: string
}

export default function NewReportPage() {
  const [summary, setSummary] = useState<MyDashboardSummary | null>(null)
  const [form, setForm] = useState<FormState>({
    name: '',
    sex: '1',
    birth_day: '',
    phone: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    getDashboard().then(setSummary).catch(() => undefined)
  }, [])

  const remaining = summary?.quota_remaining ?? 0
  const outOfQuota = summary != null && remaining < 1

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!form.name.trim()) {
      setError('Vui lòng nhập họ tên')
      return
    }
    if (!form.birth_day) {
      setError('Vui lòng chọn ngày sinh')
      return
    }
    if (!form.phone.trim()) {
      setError('Vui lòng nhập số điện thoại')
      return
    }

    // Backend /api/so-hoc expects birth_day in DDMMYYYY format (re.fullmatch r'\d{8}')
    const birth_day = dayjs(form.birth_day).format('DDMMYYYY')

    setSubmitting(true)
    try {
      const pdfBuffer = await numerologyApi.getMainstreamPDF({
        full_name: form.name.trim(),
        birth_day,
        phone: form.phone.trim(),
      })
      // Trigger browser download
      const blob = new Blob([pdfBuffer], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const safeName = form.name.trim().replace(/[^\p{L}\p{N}_-]+/gu, '_').slice(0, 40)
      const a = document.createElement('a')
      a.href = url
      a.download = `bao-cao-${safeName || 'than-so-hoc'}-${birth_day}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setSuccess(
        `Đã tạo báo cáo cho ${form.name.trim()}. File PDF đã được tải xuống máy.`
      )
      // Refresh quota
      getDashboard().then(setSummary).catch(() => undefined)
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as Error).message ?? 'Có lỗi xảy ra'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AccountLayout
      title="Tạo báo cáo mới"
      description="Nhập thông tin để hệ thống xuất báo cáo PDF cá nhân hoá. Mỗi báo cáo trừ 1 lượt trong gói của bạn."
    >
      {/* Quota banner */}
      <div className="mb-6 rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 to-secondary/10 p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <span className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-primary/15 text-primary shrink-0">
            <Sparkles className="w-5 h-5" />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Lượt báo cáo còn lại
            </p>
            <p className="text-2xl font-bold mt-0.5">
              {summary == null ? '—' : `${remaining} / ${summary.quota_total}`}
            </p>
            {summary?.active_package_name && (
              <p className="text-xs text-muted-foreground mt-1">
                Gói hiện tại:{' '}
                <span className="font-medium text-foreground">
                  {summary.active_package_name}
                </span>
                {summary.active_package_expires_at && (
                  <>
                    {' · '}hết hạn{' '}
                    {dayjs(summary.active_package_expires_at).format('DD/MM/YYYY')}
                  </>
                )}
              </p>
            )}
          </div>
        </div>

        {outOfQuota && (
          <div className="mt-4 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-sm">
            Bạn đã hết lượt. <a href="/shop" className="text-primary font-medium underline">Mua thêm gói</a> để tiếp tục tạo báo cáo.
          </div>
        )}
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden"
      >
        <div className="border-b border-border bg-gradient-to-r from-primary/8 via-muted/30 to-secondary/10 px-5 sm:px-6 py-3.5">
          <h2 className="font-semibold flex items-center gap-2">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(249,106,45,0.6)]" />
            Thông tin tra cứu
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Dữ liệu này dùng để tính các chỉ số thần số học — vui lòng kiểm tra kỹ trước khi gửi.
          </p>
        </div>

        <div className="px-5 sm:px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2 space-y-1.5">
            <Label htmlFor="full_name">
              Họ và tên khai sinh <span className="text-destructive">*</span>
            </Label>
            <Input
              id="full_name"
              autoComplete="name"
              placeholder="Nguyễn Văn A"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className={FIELD_CLS}
              disabled={submitting}
            />
            <p className="text-xs text-muted-foreground">
              Nên nhập không dấu để khớp với hệ thống nội bộ.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="sex">Giới tính</Label>
            <NativeSelect
              id="sex"
              value={form.sex}
              onChange={(e) =>
                setForm({ ...form, sex: e.target.value as FormState['sex'] })
              }
              className="h-10 bg-muted/40"
              disabled={submitting}
            >
              <option value="1">Nam</option>
              <option value="2">Nữ</option>
            </NativeSelect>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="birth_day">
              Ngày sinh dương lịch <span className="text-destructive">*</span>
            </Label>
            <Input
              id="birth_day"
              type="date"
              autoComplete="bday"
              value={form.birth_day}
              onChange={(e) => setForm({ ...form, birth_day: e.target.value })}
              max={dayjs().format('YYYY-MM-DD')}
              min="1900-01-01"
              className={FIELD_CLS}
              disabled={submitting}
            />
          </div>

          <div className="sm:col-span-2 space-y-1.5">
            <Label htmlFor="phone">
              Số điện thoại <span className="text-destructive">*</span>
            </Label>
            <Input
              id="phone"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder="09xxxxxxxx"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className={FIELD_CLS}
              disabled={submitting}
            />
          </div>
        </div>

        {error && (
          <div className="mx-5 sm:mx-6 mb-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}
        {success && (
          <div className="mx-5 sm:mx-6 mb-3 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            {success}
          </div>
        )}

        <div className="border-t border-border bg-muted/20 px-5 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            Mỗi lần tạo báo cáo trừ <span className="font-medium text-foreground">1 lượt</span> từ gói.
          </p>
          <Button
            type="submit"
            size="lg"
            disabled={submitting || outOfQuota}
            className="min-w-[180px]"
          >
            {submitting ? 'Đang tạo PDF...' : 'Tạo & tải báo cáo'}
          </Button>
        </div>
      </form>
    </AccountLayout>
  )
}
