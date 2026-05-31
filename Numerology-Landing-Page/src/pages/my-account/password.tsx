/**
 * Change password — /my-account/password
 */
import { KeyRound } from 'lucide-react'
import { useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { changePassword } from '@/lib/my-account-api'

export default function ChangePasswordPage() {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(
    null,
  )

  const tooShort = newPw.length > 0 && newPw.length < 8
  const mismatch = confirmPw.length > 0 && confirmPw !== newPw
  const canSubmit =
    oldPw.length > 0 &&
    newPw.length >= 8 &&
    confirmPw === newPw &&
    !saving

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    setSaving(true)
    setMessage(null)
    try {
      await changePassword(oldPw, newPw)
      setOldPw('')
      setNewPw('')
      setConfirmPw('')
      setMessage({ kind: 'ok', text: 'Đã đổi mật khẩu thành công.' })
    } catch (err) {
      setMessage({ kind: 'err', text: (err as Error).message || 'Đổi mật khẩu thất bại.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <AccountLayout title="Đổi mật khẩu" description="Bảo mật tài khoản của bạn">
      <form
        onSubmit={handleSubmit}
        className="max-w-md rounded-xl border border-border bg-card p-6 space-y-4"
      >
        <div className="flex items-center gap-2 mb-2">
          <KeyRound className="w-5 h-5 text-primary" />
          <h2 className="font-semibold">Mật khẩu mới</h2>
        </div>

        <div>
          <Label htmlFor="old-pw">Mật khẩu hiện tại</Label>
          <Input
            id="old-pw"
            type="password"
            autoComplete="current-password"
            value={oldPw}
            onChange={(e) => setOldPw(e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="new-pw">Mật khẩu mới</Label>
          <Input
            id="new-pw"
            type="password"
            autoComplete="new-password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
          />
          <p
            className={
              'text-xs mt-1 ' +
              (tooShort ? 'text-red-600' : 'text-muted-foreground')
            }
          >
            Tối thiểu 8 ký tự.
          </p>
        </div>

        <div>
          <Label htmlFor="confirm-pw">Xác nhận mật khẩu mới</Label>
          <Input
            id="confirm-pw"
            type="password"
            autoComplete="new-password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            required
          />
          {mismatch && (
            <p className="text-xs text-red-600 mt-1">
              Mật khẩu xác nhận không khớp.
            </p>
          )}
        </div>

        <Button type="submit" disabled={!canSubmit} className="w-full">
          {saving ? 'Đang đổi...' : 'Đổi mật khẩu'}
        </Button>

        {message && (
          <p
            className={
              'text-sm ' +
              (message.kind === 'ok' ? 'text-green-700' : 'text-red-600')
            }
            role="status"
          >
            {message.text}
          </p>
        )}
      </form>
    </AccountLayout>
  )
}
