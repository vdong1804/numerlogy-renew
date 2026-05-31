/**
 * Admin order detail — /admin/orders/[id]
 * Actions: Mark-as-Paid fallback + Refund (with reason input, POST /admin/orders/{id}/refund).
 */
import { useRouter } from 'next/router'
import { useEffect, useRef, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import { toast } from '@/components/admin/admin-toast'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import {
  getAdminOrder,
  markOrderPaid,
  refundOrder,
  type AdminOrderSummary,
} from '@/lib/admin-dashboard-api'
import { formatVnd } from '@/lib/utils'

export default function AdminOrderDetailPage() {
  const router = useRouter()
  const id = Number(router.query.id)
  const [order, setOrder] = useState<AdminOrderSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Mark-paid dialog state
  const [showMarkPaid, setShowMarkPaid] = useState(false)
  const [submittingPaid, setSubmittingPaid] = useState(false)

  // Refund dialog state
  const [showRefund, setShowRefund] = useState(false)
  const [refundReason, setRefundReason] = useState('')
  const [submittingRefund, setSubmittingRefund] = useState(false)
  const reasonRef = useRef<HTMLTextAreaElement>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      setOrder(await getAdminOrder(id))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!id || Number.isNaN(id)) return
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const handleMarkPaid = async () => {
    setSubmittingPaid(true)
    try {
      await markOrderPaid(id)
      toast.success('Đã đánh dấu thanh toán + chạy fulfillment')
      setShowMarkPaid(false)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSubmittingPaid(false)
    }
  }

  const openRefundDialog = () => {
    setRefundReason('')
    setShowRefund(true)
    // Focus reason textarea after dialog mounts
    setTimeout(() => reasonRef.current?.focus(), 100)
  }

  const handleRefund = async () => {
    if (!refundReason.trim()) {
      toast.error('Vui lòng nhập lý do hoàn tiền')
      return
    }
    setSubmittingRefund(true)
    try {
      await refundOrder(id, refundReason.trim())
      toast.success('Yêu cầu hoàn tiền đã được gửi')
      setShowRefund(false)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSubmittingRefund(false)
    }
  }

  return (
    <AdminLayout title={`Đơn hàng #${id}`}>
      <AdminPageHeader title={`Đơn hàng #${id}`} backHref="/admin/orders">
        {order && order.status === 'pending' && (
          <Button onClick={() => setShowMarkPaid(true)} variant="outline">
            Đánh dấu đã thanh toán
          </Button>
        )}
        {order && order.status === 'paid' && (
          <Button onClick={openRefundDialog} variant="outline" className="text-destructive border-destructive hover:bg-destructive/10">
            Hoàn tiền
          </Button>
        )}
      </AdminPageHeader>

      <ErrorBanner message={error} />

      {loading || !order ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-4 max-w-3xl">
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg">{order.ref_code}</span>
            <Badge variant={order.status === 'paid' ? 'default' : 'outline'}>{order.status}</Badge>
            <span className="text-sm text-muted-foreground">User #{order.user_id}</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-3">Items</h2>
            <ul className="divide-y divide-border">
              {order.items.map((it) => (
                <li key={it.id} className="py-2 flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium">{it.snapshot_name}</p>
                    <p className="text-xs text-muted-foreground">SP #{it.product_id} · x{it.qty}</p>
                  </div>
                  <span className="font-semibold">{formatVnd(it.unit_price * it.qty)}</span>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between pt-3 border-t border-border mt-3">
              <span className="font-semibold">Tổng</span>
              <span className="font-bold text-xl text-primary">{formatVnd(order.total_amount)}</span>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-3">Metadata</h2>
            <pre className="text-xs bg-muted/40 p-3 rounded overflow-auto">
{JSON.stringify(order.meta, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Mark-paid confirm dialog */}
      <ConfirmDialog
        open={showMarkPaid}
        title="Đánh dấu đã thanh toán?"
        message={`Hệ thống sẽ cộng quota / render báo cáo cho đơn ${order?.ref_code}. Hành động này không thể hoàn tác.`}
        confirmLabel="Xác nhận"
        loading={submittingPaid}
        onConfirm={handleMarkPaid}
        onCancel={() => setShowMarkPaid(false)}
      />

      {/* Refund dialog — requires reason input */}
      <Dialog open={showRefund} onOpenChange={(o) => !o && setShowRefund(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Hoàn tiền đơn {order?.ref_code}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <p className="text-sm text-muted-foreground">
              Thao tác này sẽ gửi yêu cầu hoàn{' '}
              <strong>{order ? formatVnd(order.total_amount) : ''}</strong> về tài khoản khách.
              Vui lòng nhập lý do để lưu vào audit log.
            </p>
            <div>
              <label className="text-sm font-medium mb-1 block" htmlFor="refund-reason">
                Lý do hoàn tiền <span className="text-destructive">*</span>
              </label>
              <textarea
                id="refund-reason"
                ref={reasonRef}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Ví dụ: Khách chưa nhận được báo cáo do lỗi hệ thống..."
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                disabled={submittingRefund}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRefund(false)} disabled={submittingRefund}>
              Hủy
            </Button>
            <Button
              variant="destructive"
              onClick={handleRefund}
              disabled={submittingRefund || !refundReason.trim()}
            >
              {submittingRefund ? 'Đang xử lý...' : 'Xác nhận hoàn tiền'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  )
}
