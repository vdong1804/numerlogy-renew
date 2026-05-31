/**
 * Admin payment detail page with approve/reject.
 * Route: /admin/payments/[id]
 */
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import PaymentApprovalCard, { type Payment } from '@/components/admin/payment-approval-card'
import { Skeleton } from '@/components/ui/skeleton'
import { getJson } from '@/lib/admin-api'

export default function PaymentDetailPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [payment, setPayment] = useState<Payment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getJson<Payment>(`/admin/payments/${id}`)
      .then(setPayment)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <AdminLayout title={`Thanh toán #${id}`}>
      <AdminPageHeader title={`Thanh toán #${id}`} description="Xem chi tiết và phê duyệt" backHref="/admin/payments" />
      <ErrorBanner message={error} />
      <div className="max-w-2xl">
        {loading ? (
          <Skeleton className="h-56 w-full rounded-xl" />
        ) : (
          payment && (
            <PaymentApprovalCard
              payment={payment}
              onStatusChange={(updated) => setPayment(updated)}
            />
          )
        )}
      </div>
    </AdminLayout>
  )
}
