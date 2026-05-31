/**
 * Dashboard mini-charts — payments trend (area) + status breakdown (bar).
 */
import * as React from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatVnd } from '@/lib/utils'

export interface PaymentTrendPoint {
  date: string
  count: number
  amount: number
}

export interface StatusBreakdownPoint {
  status: string
  value: number
  color: string
}

interface PaymentsTrendChartProps {
  data: PaymentTrendPoint[]
  loading?: boolean
}

export function PaymentsTrendChart({ data, loading }: PaymentsTrendChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Xu hướng thanh toán</CardTitle>
        <CardDescription>14 ngày gần nhất · Số giao dịch theo ngày</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-[220px] w-full" />
        ) : data.length === 0 ? (
          <EmptyChart>Chưa có giao dịch nào.</EmptyChart>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="paymentsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={32}
              />
              <Tooltip
                contentStyle={{
                  background: 'hsl(var(--popover))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: 8,
                  fontSize: 12,
                  color: 'hsl(var(--popover-foreground))',
                }}
                formatter={(val: number, name: string) =>
                  name === 'amount' ? formatVnd(val) : val.toLocaleString('vi-VN')
                }
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fill="url(#paymentsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

interface StatusBreakdownChartProps {
  data: StatusBreakdownPoint[]
  loading?: boolean
}

export function StatusBreakdownChart({ data, loading }: StatusBreakdownChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trạng thái thanh toán</CardTitle>
        <CardDescription>Phân bổ theo trạng thái</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-[220px] w-full" />
        ) : data.every((d) => d.value === 0) ? (
          <EmptyChart>Chưa có dữ liệu.</EmptyChart>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="status"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={32}
              />
              <Tooltip
                contentStyle={{
                  background: 'hsl(var(--popover))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: 8,
                  fontSize: 12,
                  color: 'hsl(var(--popover-foreground))',
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {data.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

function EmptyChart({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-center h-[220px] text-sm text-muted-foreground border border-dashed border-border rounded-lg">
      {children}
    </div>
  )
}
