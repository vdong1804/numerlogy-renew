/**
 * Admin user detail page.
 * Route: /admin/users/[id]
 */
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import { Check, Download, Mail, Shield, User as UserIcon, X } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { getJson } from '@/lib/admin-api'
import { formatDateTimeVi } from '@/lib/utils'

interface UserDetail {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  downloads_remaining?: number
}

export default function UserDetailPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [user, setUser] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getJson<UserDetail>(`/admin/users/${id}`)
      .then(setUser)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <AdminLayout title={`Người dùng #${id}`}>
      <AdminPageHeader title={`Người dùng #${id}`} description="Thông tin tài khoản & quyền hạn" backHref="/admin/users" />
      <ErrorBanner message={error} />

      {loading ? (
        <Skeleton className="h-72 w-full max-w-2xl" />
      ) : user ? (
        <div className="grid gap-4 max-w-2xl">
          <Card>
            <CardHeader className="flex flex-row items-center gap-4 space-y-0">
              <span className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-primary to-accent-foreground/70 text-primary-foreground text-lg font-semibold shadow-sm">
                {(user.full_name || user.email).slice(0, 1).toUpperCase()}
              </span>
              <div className="min-w-0">
                <CardTitle className="text-lg truncate">{user.full_name || 'Chưa đặt tên'}</CardTitle>
                <CardDescription className="flex items-center gap-1.5 mt-1">
                  <Mail className="w-3.5 h-3.5" />
                  <span className="truncate">{user.email}</span>
                </CardDescription>
              </div>
              <div className="ml-auto flex flex-wrap gap-1.5 justify-end">
                {user.is_active ? (
                  <Badge variant="success" className="gap-1">
                    <Check className="w-3 h-3" /> Kích hoạt
                  </Badge>
                ) : (
                  <Badge variant="destructive" className="gap-1">
                    <X className="w-3 h-3" /> Khóa
                  </Badge>
                )}
                {user.is_superuser && (
                  <Badge variant="accent" className="gap-1">
                    <Shield className="w-3 h-3" /> Admin
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <Separator className="mb-4" />
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                <InfoRow icon={<UserIcon className="w-4 h-4" />} label="ID người dùng" value={`#${user.id}`} />
                <InfoRow
                  icon={<Download className="w-4 h-4" />}
                  label="Lượt tải còn lại"
                  value={user.downloads_remaining != null ? user.downloads_remaining.toString() : '—'}
                />
                <InfoRow label="Vai trò" value={user.is_superuser ? 'Quản trị viên' : 'Người dùng'} />
                <InfoRow label="Ngày tạo" value={formatDateTimeVi(user.created_at)} />
              </dl>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </AdminLayout>
  )
}

function InfoRow({ icon, label, value }: { icon?: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground font-medium">
        {icon}
        {label}
      </dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  )
}
