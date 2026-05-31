/**
 * Profile edit — /my-account/profile
 * Password change is on its own page: /my-account/password
 */
import Link from 'next/link'
import { CheckCircle2, KeyRound, UserCog, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  getMyProfile,
  updateMyProfile,
  type MyProfile,
  type MyProfileUpdate,
} from '@/lib/my-account-api'

export default function MyProfilePage() {
  const [form, setForm] = useState<MyProfileUpdate>({
    name: '',
    birth_day: '',
    phone: '',
    address: '',
  })
  const [profile, setProfile] = useState<MyProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(
    null,
  )

  useEffect(() => {
    getMyProfile()
      .then((p) => {
        setProfile(p)
        setForm({
          name: p.name || '',
          birth_day: p.birth_day || '',
          phone: p.phone || '',
          address: p.address || '',
        })
      })
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const updated = await updateMyProfile(form)
      setProfile(updated)
      setMessage({ kind: 'ok', text: 'Đã lưu thay đổi.' })
    } catch (err) {
      setMessage({ kind: 'err', text: (err as Error).message || 'Lưu thất bại.' })
    } finally {
      setSaving(false)
    }
  }

  // Shared input styling — soft tinted bg + slightly taller, so fields read
  // clearly against the white card without needing a heavy border.
  const fieldCls = 'h-10 bg-muted/40'

  return (
    <AccountLayout title="Hồ sơ" description="Cập nhật thông tin cá nhân">
      {loading ? (
        <div className="max-w-3xl space-y-4">
          <Skeleton className="h-10 w-1/3" />
          <Skeleton className="h-72 w-full rounded-xl" />
        </div>
      ) : (
        <form
          onSubmit={handleSave}
          className="max-w-3xl rounded-xl border border-border bg-card shadow-md overflow-hidden"
        >
          {/* Card header */}
          <div className="flex items-center gap-2.5 border-b border-border bg-muted/30 px-5 sm:px-6 py-3.5">
            <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
              <UserCog className="w-4 h-4" />
            </span>
            <div>
              <h2 className="font-semibold leading-tight">Thông tin cá nhân</h2>
              <p className="text-xs text-muted-foreground">Các thông tin này hiển thị trong báo cáo & đơn hàng.</p>
            </div>
          </div>

          {/* Card body */}
          <div className="px-5 sm:px-6 py-6 space-y-5">
            {/* Email (read-only, full width) */}
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profile?.email ?? ''}
                disabled
                autoComplete="email"
                className={fieldCls}
              />
              <p className="text-xs text-muted-foreground">
                Email không thể thay đổi.
              </p>
            </div>

            {/* Name + Birth date in 2 cols on md+ */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="name">Họ và tên</Label>
                <Input
                  id="name"
                  type="text"
                  autoComplete="name"
                  placeholder="Nguyễn Văn A"
                  value={form.name ?? ''}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className={fieldCls}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="birth_day">Ngày sinh</Label>
                <Input
                  id="birth_day"
                  type="date"
                  autoComplete="bday"
                  value={form.birth_day ?? ''}
                  onChange={(e) => setForm({ ...form, birth_day: e.target.value })}
                  className={fieldCls}
                />
              </div>
            </div>

            {/* Phone */}
            <div className="space-y-1.5">
              <Label htmlFor="phone">Số điện thoại</Label>
              <Input
                id="phone"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="0xxx xxx xxx"
                value={form.phone ?? ''}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className={fieldCls}
              />
            </div>

            {/* Address — multi-line */}
            <div className="space-y-1.5">
              <Label htmlFor="address">Địa chỉ</Label>
              <Textarea
                id="address"
                rows={3}
                autoComplete="street-address"
                placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành"
                value={form.address ?? ''}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                className="bg-muted/40"
              />
            </div>

            {/* Inline status message */}
            {message && (
              <div
                role="status"
                className={
                  'flex items-start gap-2 rounded-md border px-3 py-2 text-sm ' +
                  (message.kind === 'ok'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : 'border-red-200 bg-red-50 text-red-700')
                }
              >
                {message.kind === 'ok' ? (
                  <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                )}
                <span>{message.text}</span>
              </div>
            )}
          </div>

          {/* Card footer */}
          <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-between gap-3 border-t border-border bg-muted/40 px-5 sm:px-6 py-4">
            <Link
              href="/my-account/password"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              <KeyRound className="w-4 h-4" />
              Đổi mật khẩu
            </Link>
            <Button type="submit" disabled={saving} className="w-full sm:w-auto min-w-[140px]">
              {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          </div>
        </form>
      )}
    </AccountLayout>
  )
}
