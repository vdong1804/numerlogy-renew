/**
 * Recharts visualisations for /admin/chatbot/analytics.
 *
 * Two charts:
 *  - DailyMessagesChart: stacked bar of messages by tier per day
 *  - CostByModelChart: horizontal bar of estimated USD cost per model
 */
import * as React from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

import type { AnalyticsOverview, CostByModel, DailyMessageStat } from './chatbot-types'

const TIER_COLORS: Record<string, string> = {
  free: 'hsl(217 91% 60%)',
  paid: 'hsl(142 71% 45%)',
  unknown: 'hsl(220 9% 46%)',
}

const MODEL_PALETTE = [
  'hsl(217 91% 60%)',
  'hsl(142 71% 45%)',
  'hsl(38 92% 50%)',
  'hsl(0 84% 60%)',
  'hsl(280 70% 55%)',
]

interface DailyPoint {
  day: string
  free: number
  paid: number
  unknown: number
}

/**
 * Pivot the long-form daily breakdown into one row per day with one column
 * per tier so recharts can stack them.
 */
function pivotDaily(stats: DailyMessageStat[]): DailyPoint[] {
  const byDay = new Map<string, DailyPoint>()
  for (const s of stats) {
    const row = byDay.get(s.day) ?? { day: s.day, free: 0, paid: 0, unknown: 0 }
    if (s.tier === 'free') row.free += s.count
    else if (s.tier === 'paid') row.paid += s.count
    else row.unknown += s.count
    byDay.set(s.day, row)
  }
  return Array.from(byDay.values()).sort((a, b) => (a.day < b.day ? -1 : 1))
}

interface Props {
  data: AnalyticsOverview | null
  loading?: boolean
}

export function DailyMessagesChart({ data, loading }: Props) {
  const points = data ? pivotDaily(data.messages_by_day) : []
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Tin nhắn theo ngày</CardTitle>
        <CardDescription>Stack theo tier (free / paid)</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : points.length === 0 ? (
          <p className="text-sm text-muted-foreground">Không có dữ liệu.</p>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={points} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  cursor={{ fill: 'hsl(var(--accent) / 0.4)' }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="free" stackId="t" fill={TIER_COLORS.free} name="Free" />
                <Bar dataKey="paid" stackId="t" fill={TIER_COLORS.paid} name="Paid" />
                <Bar dataKey="unknown" stackId="t" fill={TIER_COLORS.unknown} name="Khác" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function CostByModelChart({ data, loading }: Props) {
  const rows: CostByModel[] = data?.cost_by_model ?? []
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Chi phí theo model</CardTitle>
        <CardDescription>USD ước tính trong cửa sổ</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">Không có dữ liệu.</p>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={rows}
                margin={{ top: 8, right: 16, left: 40, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis dataKey="model" type="category" tick={{ fontSize: 10 }} width={120} />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  formatter={(v: number) => [`$${v.toFixed(4)}`, 'USD']}
                />
                <Bar dataKey="estimated_usd" name="USD">
                  {rows.map((_, idx) => (
                    <Cell key={idx} fill={MODEL_PALETTE[idx % MODEL_PALETTE.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
