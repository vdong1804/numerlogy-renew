/**
 * Order list — /my-account/orders
 */
import ShoppingBagOutlinedIcon from '@mui/icons-material/ShoppingBagOutlined'
import Link from 'next/link'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import EmptyState from '@/components/empty-state'
import OrderCardSkeleton from '@/components/skeleton/order-card-skeleton'
import { Badge } from '@/components/ui/badge'
import { listOrders, type MyOrderSummary } from '@/lib/my-account-api'
import { formatVnd } from '@/lib/utils'

const STATUS_LABEL: Record<MyOrderSummary['status'], string> = {
  pending: 'Chờ thanh toán',
  paid: 'Đã thanh toán',
  cancelled: 'Đã hủy',
  expired: 'Hết hạn',
  failed: 'Thất bại',
}

export default function MyOrdersPage() {
  const [orders, setOrders] = useState<MyOrderSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listOrders({ limit: 50 })
      .then((res) => setOrders(res.items))
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  return (
    <AccountLayout title="Đơn hàng" description="Lịch sử đơn của bạn">
      {loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <OrderCardSkeleton key={i} />
          ))}
        </div>
      ) : orders.length === 0 ? (
        <EmptyState
          icon={<ShoppingBagOutlinedIcon fontSize="inherit" />}
          title="Bạn chưa có đơn hàng nào"
          description="Khám phá các báo cáo thần số học và đặt mua ngay hôm nay."
          ctaLabel="Mua báo cáo"
          ctaHref="/shop"
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="py-2 pr-4">Mã đơn</th>
                <th className="py-2 pr-4">Trạng thái</th>
                <th className="py-2 pr-4 text-right">Tổng</th>
                <th className="py-2 pr-4">Ngày tạo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-muted/40">
                  <td className="py-2 pr-4 font-mono">
                    <Link className="text-primary hover:underline" href={`/my-account/orders/${o.id}`}>
                      {o.ref_code}
                    </Link>
                  </td>
                  <td className="py-2 pr-4">
                    <Badge variant={o.status === 'paid' ? 'default' : 'outline'}>
                      {STATUS_LABEL[o.status]}
                    </Badge>
                  </td>
                  <td className="py-2 pr-4 text-right font-semibold">
                    {formatVnd(o.total_amount)}
                  </td>
                  <td className="py-2 pr-4 text-muted-foreground">
                    {new Date(o.created_at).toLocaleDateString('vi-VN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AccountLayout>
  )
}
