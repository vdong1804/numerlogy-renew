/**
 * Admin payments list with filter tabs and approval cards.
 * Route: /admin/payments
 */
import Link from 'next/link'
import { useCallback, useEffect, useState } from 'react'
import { ArrowRight, Inbox } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import PaymentApprovalCard, { type Payment } from '@/components/admin/payment-approval-card'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { getJson } from '@/lib/admin-api'

interface PaymentsResponse {
  items: Payment[]
  total: number
}

const FILTERS = [
  { value: '1', label: 'Chờ duyệt' },
  { value: '2', label: 'Đã duyệt' },
  { value: '3', label: 'Từ chối' },
  { value: '', label: 'Tất cả' },
] as const

export default function PaymentsListPage() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('1')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ limit: '50', offset: '0' })
      if (statusFilter) params.set('status', statusFilter)
      const data = await getJson<PaymentsResponse>(`/admin/payments?${params}`)
      setPayments(data.items ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleStatusChange = (updated: Payment) => {
    setPayments((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
  }

  return (
    <AdminLayout title="Thanh toán">
      <AdminPageHeader title="Thanh toán" description="Phê duyệt giao dịch và theo dõi lịch sử">
        <div className="inline-flex items-center rounded-lg border border-border bg-card p-1">
          {FILTERS.map((f) => {
            const active = statusFilter === f.value
            return (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded-md transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {f.label}
              </button>
            )
          })}
        </div>
      </AdminPageHeader>

      <ErrorBanner message={error} />

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-xl" />
          ))}
        </div>
      ) : payments.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16 text-center">
          <span className="flex items-center justify-center w-12 h-12 rounded-full bg-muted text-muted-foreground mb-3">
            <Inbox className="w-6 h-6" />
          </span>
          <p className="text-sm font-medium">Không có thanh toán nào.</p>
          <p className="text-xs text-muted-foreground mt-1">Thử chọn bộ lọc khác để xem thêm.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {payments.map((payment) => (
            <div key={payment.id} className="relative">
              <Link
                href={`/admin/payments/${payment.id}`}
                className="absolute top-5 right-5 z-10 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                Chi tiết <ArrowRight className="w-3 h-3" />
              </Link>
              <PaymentApprovalCard payment={payment} onStatusChange={handleStatusChange} />
            </div>
          ))}
        </div>
      )}

      {total > 50 && (
        <p className="mt-4 text-xs text-muted-foreground">
          Hiển thị 50/{total.toLocaleString('vi-VN')} thanh toán. Dùng bộ lọc để thu hẹp kết quả.
        </p>
      )}
    </AdminLayout>
  )
}
