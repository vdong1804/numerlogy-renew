/**
 * Admin dashboard — stat cards + trend chart + recent activity + content shortcuts.
 */
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, BookOpen, CreditCard, Files, Users, Wallet } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { DashboardStatCard } from '@/components/admin/dashboard-stat-card'
import {
  PaymentsTrendChart,
  StatusBreakdownChart,
  type PaymentTrendPoint,
  type StatusBreakdownPoint,
} from '@/components/admin/dashboard-charts'
import {
  DashboardRecentPayments,
  type RecentPaymentRow,
} from '@/components/admin/dashboard-recent-payments'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { getJson } from '@/lib/admin-api'
import { CONTENT_RESOURCES } from '@/lib/content-resources'
import { formatVnd } from '@/lib/utils'

interface DashboardStats {
  pendingPayments: number
  totalUsers: number
  totalContent: number
  pendingAmount: number
  paymentsTrend: PaymentTrendPoint[]
  statusBreakdown: StatusBreakdownPoint[]
  recentPayments: RecentPaymentRow[]
}

interface PaymentApi {
  id: number
  amount: number
  status: number
  created_at: string
  user?: { email?: string; full_name?: string }
}

interface PaymentsListResp {
  items: PaymentApi[]
  total: number
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    Promise.all([
      getJson<PaymentsListResp>('/admin/payments?limit=200').catch(() => ({ items: [], total: 0 })),
      getJson<{ total: number }>('/admin/users?limit=1').catch(() => ({ total: 0 })),
    ]).then(([payments, users]) => {
      if (!alive) return
      setData(buildStats(payments, users.total))
      setLoading(false)
    })
    return () => { alive = false }
  }, [])

  return (
    <AdminLayout title="Tổng quan">
      <DashboardHeader />

      <section className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 mt-6">
        <DashboardStatCard
          label="Thanh toán chờ duyệt"
          value={data?.pendingPayments ?? '—'}
          href="/admin/payments"
          icon={CreditCard}
          accentClassName="bg-warning/15 text-warning"
          trendLabel="Cần phê duyệt"
          loading={loading}
        />
        <DashboardStatCard
          label="Tổng tiền chờ"
          value={data ? formatVnd(data.pendingAmount) : '—'}
          href="/admin/payments"
          icon={Wallet}
          accentClassName="bg-primary/10 text-primary"
          loading={loading}
        />
        <DashboardStatCard
          label="Người dùng"
          value={data?.totalUsers ?? '—'}
          href="/admin/users"
          icon={Users}
          accentClassName="bg-success/15 text-success"
          loading={loading}
        />
        <DashboardStatCard
          label="Bảng nội dung"
          value={CONTENT_RESOURCES.length}
          href="/admin/content/main-number"
          icon={Files}
          accentClassName="bg-accent text-accent-foreground"
          trendLabel={`${CONTENT_RESOURCES.length} resource`}
          loading={false}
        />
      </section>

      <section className="grid gap-4 grid-cols-1 lg:grid-cols-3 mt-6">
        <div className="lg:col-span-2">
          <PaymentsTrendChart data={data?.paymentsTrend ?? []} loading={loading} />
        </div>
        <StatusBreakdownChart data={data?.statusBreakdown ?? defaultStatusBreakdown()} loading={loading} />
      </section>

      <section className="grid gap-4 grid-cols-1 lg:grid-cols-3 mt-6">
        <div className="lg:col-span-2">
          <DashboardRecentPayments items={data?.recentPayments ?? []} loading={loading} />
        </div>
        <ContentShortcuts />
      </section>
    </AdminLayout>
  )
}

function DashboardHeader() {
  return (
    <div className="flex flex-col gap-1">
      <h1 className="text-2xl font-bold tracking-tight">Tổng quan</h1>
      <p className="text-sm text-muted-foreground">
        Theo dõi tình trạng thanh toán, người dùng và nội dung trong cùng một nơi.
      </p>
    </div>
  )
}

function ContentShortcuts() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
        <div>
          <CardTitle>Nội dung Thần Số Học</CardTitle>
          <CardDescription>{CONTENT_RESOURCES.length} bảng nội dung</CardDescription>
        </div>
        <Link
          href="/admin/content/main-number"
          className="text-xs text-primary font-medium hover:underline inline-flex items-center gap-1"
        >
          Vào nội dung <ArrowRight className="w-3 h-3" />
        </Link>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-2">
        {CONTENT_RESOURCES.slice(0, 8).map((r) => (
          <Link
            key={r.slug}
            href={`/admin/content/${r.slug}`}
            className="group flex items-center gap-2 rounded-lg border border-border/70 px-3 py-2 hover:border-primary/50 hover:bg-accent/40 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary" />
            <span className="text-xs font-medium truncate flex-1">{r.label}</span>
          </Link>
        ))}
        {CONTENT_RESOURCES.length > 8 && (
          <Link
            href="/admin/content/main-number"
            className="col-span-2 text-center text-xs text-muted-foreground hover:text-primary py-2"
          >
            + {CONTENT_RESOURCES.length - 8} bảng khác
          </Link>
        )}
      </CardContent>
    </Card>
  )
}

function buildStats(paymentsResp: PaymentsListResp, totalUsers: number): DashboardStats {
  const items = paymentsResp.items ?? []
  const pending = items.filter((p) => p.status === 1)
  const recent = [...items]
    .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))
    .slice(0, 10)

  // 14-day buckets
  const days: PaymentTrendPoint[] = []
  const today = new Date()
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    const dayItems = items.filter((p) => p.created_at.slice(0, 10) === key)
    days.push({
      date: `${d.getDate()}/${d.getMonth() + 1}`,
      count: dayItems.length,
      amount: dayItems.reduce((sum, p) => sum + (p.amount || 0), 0),
    })
  }

  const statusBreakdown: StatusBreakdownPoint[] = [
    { status: 'Chờ duyệt', value: items.filter((p) => p.status === 1).length, color: 'hsl(38 92% 50%)' },
    { status: 'Đã duyệt', value: items.filter((p) => p.status === 2).length, color: 'hsl(142 71% 45%)' },
    { status: 'Từ chối', value: items.filter((p) => p.status === 3).length, color: 'hsl(0 84% 60%)' },
  ]

  return {
    pendingPayments: pending.length,
    totalUsers,
    totalContent: CONTENT_RESOURCES.length,
    pendingAmount: pending.reduce((s, p) => s + (p.amount || 0), 0),
    paymentsTrend: days,
    statusBreakdown,
    recentPayments: recent,
  }
}

function defaultStatusBreakdown(): StatusBreakdownPoint[] {
  return [
    { status: 'Chờ duyệt', value: 0, color: 'hsl(38 92% 50%)' },
    { status: 'Đã duyệt', value: 0, color: 'hsl(142 71% 45%)' },
    { status: 'Từ chối', value: 0, color: 'hsl(0 84% 60%)' },
  ]
}
