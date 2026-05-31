/**
 * Account dashboard — /my-account
 */
import Link from 'next/link'
import {
  ArrowRight,
  FileText,
  ShoppingBag,
  Sparkles,
  Wand2,
  type LucideIcon,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import DashboardPackageCard from '@/components/my-account/dashboard-package-card'
import DashboardQuotaCard from '@/components/my-account/dashboard-quota-card'
import { Skeleton } from '@/components/ui/skeleton'
import { getDashboard, type MyDashboardSummary } from '@/lib/my-account-api'

export default function MyAccountDashboard() {
  const [summary, setSummary] = useState<MyDashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(setSummary)
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  return (
    <AccountLayout title="Tổng quan" description="Tài khoản của bạn">
      {loading || !summary ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-28 w-full rounded-xl" />
          <Skeleton className="h-28 w-full rounded-xl" />
          <Skeleton className="h-28 w-full rounded-xl" />
          <Skeleton className="h-28 w-full rounded-xl" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <DashboardQuotaCard
            used={summary.quota_used}
            total={summary.quota_total}
            remaining={summary.quota_remaining}
          />
          <DashboardPackageCard
            packageName={summary.active_package_name}
            quotaTotal={summary.active_package_total}
            acquiredAt={summary.active_package_acquired_at}
            expiresAt={summary.active_package_expires_at}
          />
          <StatCard
            label="Đơn hàng"
            value={`${summary.orders_count}`}
            href="/my-account/orders"
          />
          <StatCard
            label="Báo cáo đã có"
            value={`${summary.reports_count}`}
            href="/my-account/reports"
          />
        </div>
      )}

      {summary?.recent_orders && summary.recent_orders.length > 0 && (
        <section className="mt-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Đơn hàng gần đây</h2>
            <Link
              href="/my-account/orders"
              className="text-sm text-primary hover:underline"
            >
              Xem tất cả →
            </Link>
          </div>
          <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Mã đơn</th>
                  <th className="text-left px-4 py-2 font-medium">Trạng thái</th>
                  <th className="text-right px-4 py-2 font-medium">Tổng tiền</th>
                  <th className="text-left px-4 py-2 font-medium">Ngày tạo</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_orders.map((o) => (
                  <tr key={o.id} className="border-t border-border">
                    <td className="px-4 py-2">
                      <Link
                        href={`/my-account/orders/${o.id}`}
                        className="text-primary hover:underline"
                      >
                        {o.ref_code}
                      </Link>
                    </td>
                    <td className="px-4 py-2">
                      <OrderStatusBadge status={o.status} />
                    </td>
                    <td className="px-4 py-2 text-right">
                      {formatVnd(o.total_amount)}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {formatDate(o.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {summary?.recent_reports && summary.recent_reports.length > 0 && (
        <section className="mt-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Báo cáo gần đây</h2>
            <Link
              href="/my-account/reports"
              className="text-sm text-primary hover:underline"
            >
              Xem tất cả →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {summary.recent_reports.map((r) => (
              <Link
                key={r.id}
                href={`/my-account/reports/${r.id}`}
                className="rounded-xl border border-border bg-card p-4 hover:border-primary transition-colors"
              >
                <p className="font-medium text-sm">Báo cáo #{r.id}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Tạo lúc: {formatDate(r.generated_at)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Đã tải: {r.download_count} lần
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured CTA — "spend your quota" entry point */}
      {summary && summary.quota_remaining > 0 && (
        <section className="mt-10">
          <Link
            href="/my-account/new-report"
            className="group flex flex-col sm:flex-row items-start sm:items-center gap-4 rounded-2xl border border-primary/30
                       bg-gradient-to-br from-primary/12 via-card to-secondary/10 p-5 sm:p-6 shadow-sm
                       transition-all hover:shadow-md hover:-translate-y-0.5"
          >
            <span className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary text-primary-foreground shrink-0 shadow-[0_8px_20px_-6px_rgba(249,106,45,0.55)]">
              <Wand2 className="w-6 h-6" />
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-base sm:text-lg">
                Tạo báo cáo mới ngay
              </p>
              <p className="text-sm text-muted-foreground mt-0.5">
                Bạn còn{' '}
                <span className="font-semibold text-foreground">
                  {summary.quota_remaining} lượt
                </span>{' '}
                — nhập họ tên + ngày sinh để xuất báo cáo PDF cá nhân hoá.
              </p>
            </div>
            <ArrowRight className="w-5 h-5 text-primary shrink-0 transition-transform group-hover:translate-x-1" />
          </Link>
        </section>
      )}

      <section className="mt-10">
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-block w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(249,106,45,0.55)]" />
          <h2 className="text-lg font-semibold">Bắt đầu nhanh</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <QuickActionCard
            href="/my-account/new-report"
            icon={Wand2}
            title="Tạo báo cáo mới"
            description="Nhập thông tin và xuất PDF, trừ 1 lượt từ gói."
          />
          <QuickActionCard
            href="/my-account/reports"
            icon={FileText}
            title="Thư viện báo cáo"
            description="Xem lại các báo cáo đã tạo và tải về."
          />
          <QuickActionCard
            href="/shop"
            icon={Sparkles}
            title="Mua thêm báo cáo / gói"
            description="Khám phá các gói và lá số tại Cửa hàng."
          />
          <QuickActionCard
            href="/my-account/orders"
            icon={ShoppingBag}
            title="Lịch sử đơn hàng"
            description="Tra cứu trạng thái và hoá đơn đã mua."
          />
        </div>
      </section>
    </AccountLayout>
  )
}

function QuickActionCard({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string
  icon: LucideIcon
  title: string
  description: string
}) {
  return (
    <Link
      href={href}
      className="group flex items-start gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm
                 hover:border-primary/50 hover:shadow-lg hover:-translate-y-0.5 transition-all"
    >
      <span className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
        <Icon className="w-5 h-5" />
      </span>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm leading-tight">{title}</p>
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{description}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-muted-foreground shrink-0 mt-1 transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
    </Link>
  )
}

function StatCard({ label, value, href }: { label: string; value: string; href?: string }) {
  const body = (
    <div className="rounded-2xl border border-border bg-card p-5 h-full shadow-sm transition-all hover:border-primary/40 hover:shadow-md">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  )
  return href ? <Link href={href}>{body}</Link> : body
}

function OrderStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    paid: { label: 'Đã thanh toán', cls: 'bg-green-100 text-green-700' },
    pending: { label: 'Chờ thanh toán', cls: 'bg-yellow-100 text-yellow-700' },
    cancelled: { label: 'Đã huỷ', cls: 'bg-gray-100 text-gray-700' },
    expired: { label: 'Hết hạn', cls: 'bg-gray-100 text-gray-700' },
    failed: { label: 'Thất bại', cls: 'bg-red-100 text-red-700' },
  }
  const info = map[status] ?? { label: status, cls: 'bg-gray-100 text-gray-700' }
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${info.cls}`}>
      {info.label}
    </span>
  )
}

function formatVnd(n: number): string {
  return `${new Intl.NumberFormat('vi-VN').format(n)} ₫`
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso.slice(0, 16).replace('T', ' ')
  }
}
