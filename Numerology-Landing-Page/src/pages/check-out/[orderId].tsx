/**
 * Order checkout page — /check-out/[orderId]
 *
 * Shows the QR placeholder, the ref_code copy box, the totals, and live
 * polls /api/orders/:id/status until the order resolves (paid/expired/...).
 */
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Phone,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'

import useOrderStatusPoller from '@/components/checkout/order-status-poller'
import QrDisplay from '@/components/checkout/qr-display'
import RefCodeCopy from '@/components/checkout/ref-code-copy'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { getOrder, type Order } from '@/lib/shop-api'
import { formatVnd } from '@/lib/utils'
import type { NextPageWithLayout } from '@/models'

const STATUS_INFO: Record<
  Order['status'],
  {
    label: string
    badgeCls: string
    bannerCls: string
    icon: typeof Clock
  }
> = {
  pending: {
    label: 'Chờ thanh toán',
    badgeCls: 'border-warning/40 text-warning bg-warning/10',
    bannerCls: 'border-warning/30 bg-warning/10 text-foreground',
    icon: Clock,
  },
  paid: {
    label: 'Đã thanh toán',
    badgeCls: 'border-success/40 text-success bg-success/10',
    bannerCls: 'border-success/30 bg-success/10 text-foreground',
    icon: CheckCircle2,
  },
  cancelled: {
    label: 'Đã hủy',
    badgeCls: 'border-destructive/40 text-destructive bg-destructive/10',
    bannerCls: 'border-destructive/30 bg-destructive/10 text-foreground',
    icon: XCircle,
  },
  expired: {
    label: 'Hết hạn',
    badgeCls: 'border-destructive/40 text-destructive bg-destructive/10',
    bannerCls: 'border-destructive/30 bg-destructive/10 text-foreground',
    icon: XCircle,
  },
  failed: {
    label: 'Thất bại',
    badgeCls: 'border-destructive/40 text-destructive bg-destructive/10',
    bannerCls: 'border-destructive/30 bg-destructive/10 text-foreground',
    icon: XCircle,
  },
}

const CheckoutOrderPage: NextPageWithLayout = () => {
  const router = useRouter()
  const orderId = Number(router.query.orderId)
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!orderId || Number.isNaN(orderId)) return
    setLoading(true)
    getOrder(orderId)
      .then(setOrder)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [orderId])

  const poller = useOrderStatusPoller({
    orderId: orderId || 0,
    initialStatus: order?.status,
    onResolved: (info) => {
      if (info.status !== 'paid') return
      const hasReport = (order?.items ?? []).some((it) =>
        it.snapshot_name?.toLowerCase().includes('báo cáo'),
      )
      const target = hasReport ? '/my-account/reports' : '/my-account'
      setTimeout(() => router.push(target), 2500)
    },
  })

  useEffect(() => {
    if (!order) return
    if (poller.status !== order.status) {
      getOrder(order.id).then(setOrder).catch(() => undefined)
    }
  }, [poller.status, order])

  // Free / already-paid orders should never sit on the QR page.
  // Direct-link visits land here too, so guard at the page level.
  useEffect(() => {
    if (!order) return
    const isFreePaid = order.total_amount === 0 || order.status === 'paid'
    if (!isFreePaid) return
    const hasReport = order.items.some((it) =>
      it.snapshot_name?.toLowerCase().includes('báo cáo'),
    )
    router.replace(hasReport ? '/my-account/reports' : '/my-account')
  }, [order, router])

  if (loading) {
    return (
      <div className="account-shell min-h-[70vh]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-10 w-72" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-96 w-full rounded-xl" />
            <Skeleton className="h-96 w-full rounded-xl" />
          </div>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="account-shell min-h-[70vh]">
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <XCircle className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
          <h1 className="text-xl font-semibold">Không tìm thấy đơn hàng</h1>
          {error && <p className="text-destructive text-sm mt-3">{error}</p>}
          <Button asChild variant="outline" className="mt-6">
            <Link href="/shop">
              <ArrowLeft className="w-4 h-4" /> Về cửa hàng
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const currentStatus = poller.status ?? order.status
  const statusInfo = STATUS_INFO[currentStatus] ?? STATUS_INFO.pending
  const StatusIcon = statusInfo.icon

  return (
    <div className="account-shell min-h-[70vh]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Breadcrumb */}
        <Link
          href="/shop"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" /> Tiếp tục mua sắm
        </Link>

        {/* Header */}
        <header className="mb-6">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Thanh toán đơn hàng
            </h1>
            <Badge
              variant="outline"
              className={`${statusInfo.badgeCls} inline-flex items-center gap-1.5`}
            >
              <StatusIcon className="w-3.5 h-3.5" />
              {statusInfo.label}
            </Badge>
          </div>
          <div className="h-[3px] w-12 bg-primary rounded-full mt-2" />
        </header>

        {/* Status banner for resolved states */}
        {currentStatus === 'paid' && (
          <div
            className={`flex items-start gap-3 rounded-xl border ${statusInfo.bannerCls} px-4 py-3 mb-6`}
          >
            <CheckCircle2 className="w-5 h-5 text-success shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">Thanh toán thành công!</p>
              <p className="text-muted-foreground">
                Cảm ơn bạn. Hệ thống sẽ chuyển sang trang báo cáo trong giây
                lát...
              </p>
            </div>
          </div>
        )}
        {(currentStatus === 'expired' || currentStatus === 'failed') && (
          <div
            className={`flex items-start gap-3 rounded-xl border ${statusInfo.bannerCls} px-4 py-3 mb-6`}
          >
            <XCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">
                {currentStatus === 'expired'
                  ? 'Đơn hàng đã hết hạn'
                  : 'Thanh toán thất bại'}
              </p>
              <p className="text-muted-foreground">
                Vui lòng tạo đơn mới hoặc liên hệ hỗ trợ.
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* LEFT — QR + ref code */}
          <div className="space-y-4">
            <QrDisplay amount={order.total_amount} refCode={order.ref_code} />
            <RefCodeCopy refCode={order.ref_code} />
          </div>

          {/* RIGHT — order summary */}
          <aside>
            <div className="rounded-2xl border border-border bg-card shadow-md overflow-hidden">
              <div className="border-b border-border bg-gradient-to-r from-primary/8 via-muted/30 to-secondary/10 px-5 py-3.5">
                <h2 className="font-semibold flex items-center gap-2">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(249,106,45,0.6)]" />
                  Chi tiết đơn hàng
                </h2>
              </div>

              <ul className="divide-y divide-border px-5">
                {order.items.map((it) => (
                  <li
                    key={it.id}
                    className="py-3 flex items-start justify-between gap-3 text-sm"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">
                        {it.snapshot_name}
                      </p>
                      <p className="text-muted-foreground text-xs mt-0.5">
                        Số lượng: {it.qty}
                      </p>
                    </div>
                    <span className="font-semibold text-foreground shrink-0">
                      {formatVnd(it.unit_price * it.qty)}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="border-t border-border px-5 py-4 flex items-center justify-between">
                <span className="font-semibold text-base">Tổng cộng</span>
                <span className="font-bold text-primary text-2xl">
                  {formatVnd(order.total_amount)}
                </span>
              </div>

              <div className="border-t border-border bg-muted/20 px-5 py-4 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Mã đơn</span>
                  <span className="font-mono font-medium text-foreground">
                    {order.ref_code}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Hết hạn</span>
                  <span className="text-foreground">
                    {new Date(order.expires_at).toLocaleString('vi-VN')}
                  </span>
                </div>
              </div>

              {poller.stopped && currentStatus === 'pending' && (
                <p className="px-5 pb-3 text-xs text-muted-foreground">
                  Đã dừng kiểm tra tự động sau 30 phút. Bấm "Làm mới" nếu đã
                  chuyển khoản.
                </p>
              )}

              <div className="px-5 pb-5">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => poller.refresh()}
                >
                  <RefreshCw className="w-4 h-4" />
                  Làm mới trạng thái
                </Button>
              </div>
            </div>

            {/* Support box */}
            <div className="mt-4 rounded-xl border border-border bg-card p-4 text-sm">
              <p className="font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-primary" />
                Cần hỗ trợ?
              </p>
              <p className="text-muted-foreground text-xs leading-relaxed">
                Gọi hotline nếu chuyển khoản không tự cập nhật sau vài phút.
              </p>
              <a
                href="tel:0339387373"
                className="mt-2 inline-flex items-center gap-1.5 font-semibold text-primary hover:underline"
              >
                <Phone className="w-4 h-4" />
                0339 387 373
              </a>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

CheckoutOrderPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main meta={<Meta title="Thanh toán đơn hàng" description="Hoàn tất thanh toán" />}>
      {page}
    </Main>
  )
}

export default CheckoutOrderPage
