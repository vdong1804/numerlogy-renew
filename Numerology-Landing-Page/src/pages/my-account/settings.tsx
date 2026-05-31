/**
 * Notification settings — /my-account/settings
 */
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  getNotifications,
  updateNotifications,
  type NotificationPrefs,
} from '@/lib/my-account-api'

const DEFAULT: NotificationPrefs = {
  order_paid_email: true,
  quota_low_email: true,
  marketing_email: false,
}

export default function MySettingsPage() {
  const [prefs, setPrefs] = useState<NotificationPrefs>(DEFAULT)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getNotifications()
      .then(setPrefs)
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  const toggle = (key: keyof NotificationPrefs) => {
    setPrefs((p) => ({ ...p, [key]: !p[key] }))
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    try {
      await updateNotifications(prefs)
      setMessage('Đã lưu')
    } catch (err) {
      setMessage((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <AccountLayout title="Thông báo" description="Quản lý email gửi đến bạn">
      {loading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-3 max-w-xl">
          {([
            ['order_paid_email', 'Email xác nhận thanh toán'],
            ['quota_low_email', 'Email khi quota gần hết'],
            ['marketing_email', 'Email khuyến mãi / cập nhật sản phẩm'],
          ] as const).map(([key, label]) => (
            <label
              key={key}
              className="flex items-center justify-between rounded-lg border border-border px-4 py-3 cursor-pointer hover:bg-muted/40"
            >
              <Label className="cursor-pointer">{label}</Label>
              <input
                type="checkbox"
                checked={prefs[key]}
                onChange={() => toggle(key)}
                className="h-4 w-4"
              />
            </label>
          ))}
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
          </Button>
          {message && <p className="text-xs text-muted-foreground">{message}</p>}
        </div>
      )}
    </AccountLayout>
  )
}
