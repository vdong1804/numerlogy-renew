/**
 * Order detail — /my-account/orders/[id]
 */
import { Download } from 'lucide-react'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  downloadInvoiceBlob,
  getOrderDetail,
  type MyOrderDetail,
} from '@/lib/my-account-api'
import { formatVnd } from '@/lib/utils'

export default function MyOrderDetailPage() {
  const router = useRouter()
  const id = Number(router.query.id)
  const [order, setOrder] = useState<MyOrderDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloadingInvoice, setDownloadingInvoice] = useState(false)

  useEffect(() => {
    if (!id || Number.isNaN(id)) return
    getOrderDetail(id)
      .then(setOrder)
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [id])

  const handleInvoice = async () => {
    if (!order) return
    setDownloadingInvoice(true)
    try {
      const blob = await downloadInvoiceBlob(order.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice-${order.ref_code}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // best-effort
    } finally {
      setDownloadingInvoice(false)
    }
  }

  return (
    <AccountLayout title="Chi tiết đơn hàng">
      {loading ? (
        <Skeleton className="h-64 w-full rounded-xl" />
      ) : !order ? (
        <p>Không tìm thấy đơn hàng.</p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-lg">{order.ref_code}</span>
            <Badge variant={order.status === 'paid' ? 'default' : 'outline'}>
              {order.status}
            </Badge>
            {order.status === 'paid' && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleInvoice}
                disabled={downloadingInvoice}
                className="ml-auto"
              >
                <Download className="w-3.5 h-3.5" />{' '}
                {downloadingInvoice ? 'Đang tải...' : 'Tải hoá đơn PDF'}
              </Button>
            )}
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold text-base mb-3">Sản phẩm</h2>
            <ul className="divide-y divide-border">
              {order.items.map((it) => (
                <li
                  key={it.id}
                  className="py-2 flex items-center justify-between text-sm"
                >
                  <div>
                    <p className="font-medium">{it.snapshot_name}</p>
                    <p className="text-xs text-muted-foreground">x{it.qty}</p>
                  </div>
                  <span className="font-semibold">
                    {formatVnd(it.unit_price * it.qty)}
                  </span>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between pt-3 border-t border-border mt-3">
              <span className="font-semibold">Tổng cộng</span>
              <span className="font-bold text-xl text-primary">
                {formatVnd(order.total_amount)}
              </span>
            </div>
          </div>

          {order.paid_at && (
            <p className="text-xs text-muted-foreground">
              Đã thanh toán: {new Date(order.paid_at).toLocaleString('vi-VN')}
            </p>
          )}
        </div>
      )}
    </AccountLayout>
  )
}
