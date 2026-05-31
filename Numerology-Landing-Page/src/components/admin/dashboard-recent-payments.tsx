/**
 * Recent payments list — compact table used on dashboard.
 */
import * as React from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDateTimeVi, formatVnd } from '@/lib/utils'

interface RecentPaymentRow {
  id: number
  amount: number
  status: number
  created_at: string
  user?: { email?: string; full_name?: string }
}

interface DashboardRecentPaymentsProps {
  items: RecentPaymentRow[]
  loading?: boolean
}

const STATUS_BADGE: Record<number, { label: string; variant: 'warning' | 'success' | 'destructive' }> = {
  1: { label: 'Chờ duyệt', variant: 'warning' },
  2: { label: 'Đã duyệt', variant: 'success' },
  3: { label: 'Từ chối', variant: 'destructive' },
}

export function DashboardRecentPayments({ items, loading }: DashboardRecentPaymentsProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
        <div>
          <CardTitle>Giao dịch gần đây</CardTitle>
          <CardDescription>10 giao dịch mới nhất</CardDescription>
        </div>
        <Link
          href="/admin/payments"
          className="text-xs text-primary font-medium hover:underline inline-flex items-center gap-1"
        >
          Tất cả <ArrowRight className="w-3 h-3" />
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="px-6 py-3 flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-6 w-16" />
              </div>
            ))
          ) : items.length === 0 ? (
            <div className="px-6 py-10 text-center text-sm text-muted-foreground">
              Chưa có giao dịch nào.
            </div>
          ) : (
            items.map((p) => {
              const badge = STATUS_BADGE[p.status] ?? { label: String(p.status), variant: 'warning' as const }
              const name = p.user?.full_name || p.user?.email || '—'
              const initial = name.slice(0, 1).toUpperCase()
              return (
                <Link
                  href={`/admin/payments/${p.id}`}
                  key={p.id}
                  className="flex items-center gap-3 px-6 py-3 hover:bg-accent/40 transition-colors"
                >
                  <span className="flex items-center justify-center w-9 h-9 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                    {initial}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      #{p.id} · {formatDateTimeVi(p.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">{formatVnd(p.amount)}</p>
                    <Badge variant={badge.variant} className="mt-0.5 text-[10px]">
                      {badge.label}
                    </Badge>
                  </div>
                </Link>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export type { RecentPaymentRow }
